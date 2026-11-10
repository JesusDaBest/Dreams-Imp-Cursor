// Offline draw test for the original Dreams body vertex and fleck pixel shaders.
#include <vulkan/vulkan.h>
#include <cmath>
#include <immintrin.h>
#define NOMINMAX
#include <UIAutomation.h>
#include <wrl/client.h>

#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "uiautomationcore.lib")
#pragma comment(lib, "user32.lib")

static VkResult CreateDrawDevice(VkPhysicalDevice physical, const VkDeviceCreateInfo* info,
                                 const VkAllocationCallbacks* allocator, VkDevice* device) {
    // The shared compute harness does not otherwise need the DrawParameters feature.
    for (auto* f = static_cast<const VkBaseInStructure*>(info->pNext); f; f = f->pNext) {
        if (f->sType == VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_1_FEATURES) {
            auto* v11 = reinterpret_cast<VkPhysicalDeviceVulkan11Features*>(
                const_cast<VkBaseInStructure*>(f));
            v11->shaderDrawParameters = VK_TRUE;
        }
    }
    VkPhysicalDeviceFeatures features = *info->pEnabledFeatures;
    features.textureCompressionBC = VK_TRUE;
    VkDeviceCreateInfo draw_info = *info;
    draw_info.pEnabledFeatures = &features;
    return vkCreateDevice(physical, &draw_info, allocator, device);
}

#define vkCreateDevice CreateDrawDevice
#define main compute_replay_main
#include "../tweak-menu-artifact/pause-image-replay/replay.cpp"
#undef main
#undef vkCreateDevice

struct DrawImage {
    Context& ctx;
    VkImage image{};
    VkDeviceMemory memory{};
    VkImageView view{};
    VkImageAspectFlags aspect;

    DrawImage(Context& c, uint32_t width, uint32_t height, uint32_t layers, uint32_t mips,
              VkFormat format, VkImageUsageFlags usage) : ctx(c),
              aspect(format == VK_FORMAT_D32_SFLOAT ? VK_IMAGE_ASPECT_DEPTH_BIT : VK_IMAGE_ASPECT_COLOR_BIT) {
        VkImageCreateInfo ci{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO};
        ci.imageType = VK_IMAGE_TYPE_2D;
        ci.format = format;
        ci.extent = {width, height, 1};
        ci.mipLevels = mips;
        ci.arrayLayers = layers;
        ci.samples = VK_SAMPLE_COUNT_1_BIT;
        ci.tiling = VK_IMAGE_TILING_OPTIMAL;
        ci.usage = usage;
        check(vkCreateImage(c.device, &ci, nullptr, &image));
        VkMemoryRequirements req{};
        vkGetImageMemoryRequirements(c.device, image, &req);
        VkMemoryAllocateInfo ai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
        ai.allocationSize = req.size;
        ai.memoryTypeIndex = c.memory_type(req.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        check(vkAllocateMemory(c.device, &ai, nullptr, &memory));
        check(vkBindImageMemory(c.device, image, memory, 0));
        VkImageViewCreateInfo vi{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};
        vi.image = image;
        vi.viewType = layers == 1 ? VK_IMAGE_VIEW_TYPE_2D : VK_IMAGE_VIEW_TYPE_2D_ARRAY;
        vi.format = format;
        vi.subresourceRange = {aspect, 0, mips, 0, layers};
        check(vkCreateImageView(c.device, &vi, nullptr, &view));
    }
    ~DrawImage() {
        vkDestroyImageView(ctx.device, view, nullptr);
        vkDestroyImage(ctx.device, image, nullptr);
        vkFreeMemory(ctx.device, memory, nullptr);
    }
    void barrier(VkCommandBuffer cmd, VkImageLayout from, VkImageLayout to,
                 uint32_t layers, uint32_t mips) {
        VkImageMemoryBarrier b{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
        b.oldLayout = from;
        b.newLayout = to;
        b.srcQueueFamilyIndex = b.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        b.image = image;
        b.subresourceRange = {aspect, 0, mips, 0, layers};
        b.srcAccessMask = from == VK_IMAGE_LAYOUT_UNDEFINED ? 0 : VK_ACCESS_MEMORY_WRITE_BIT;
        b.dstAccessMask = VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT;
        vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
                             VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, 0, 0, nullptr, 0, nullptr, 1, &b);
    }
};

using NextParticles = int (*)(void* destination, unsigned capacity, void* user);
using PresentFrame = int (*)(const void* pixels, unsigned width, unsigned height, void* user);

struct LiveFrames {
    const char* shader;
    const void* constants;
    const void* push;
    NextParticles next;
    PresentFrame present;
    void* user;
    const void* draw_constants;
    const void* light_parameters;
    const char* stick_shader;
    const void* stick_constants;
    int (*stick)(void*, unsigned, void*, void*);
    const char* eye_shader;
    const void* vertex_constants;
    const void* eye_constants;
    int (*eyes)(void*);
    const float* appearance_rgb;
};

struct TemporalResolve {
    Context& context;
    const VkExtent2D extent;
    Buffer flat;
    DrawImage frame0, frame1, depth;
    VkImageView current{};
    VkDescriptorSetLayout set_layout{};
    VkPipelineLayout layout{};
    VkDescriptorPool pool{};
    VkDescriptorSet sets[2]{};
    VkPipeline pipeline{};
    VkSampler sample{};
    unsigned ping{};
    const void* push;

    TemporalResolve(Context& c, VkExtent2D size, const DrawImage& draw, const LiveFrames& live,
                    VkCommandBuffer init)
        : context(c), extent(size), flat(c, 256),
          frame0(c, size.width, size.height, 1, 1, VK_FORMAT_R16G16B16A16_SFLOAT, frame_usage),
          frame1(c, size.width, size.height, 1, 1, VK_FORMAT_R16G16B16A16_SFLOAT, frame_usage),
          depth(c, size.width, size.height, 1, 1, VK_FORMAT_R32_SFLOAT,
                VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT),
          push(live.push) {
        std::memcpy(flat.data, live.constants, 256);
        auto* flat_u = static_cast<uint32_t*>(flat.data);
        auto* flat_f = static_cast<float*>(flat.data);
        flat_u[44] = extent.width - 1;
        flat_u[45] = extent.height - 1;
        flat_f[46] = 1.0f / extent.width;
        flat_f[47] = 1.0f / extent.height;
        const VkImageSubresourceRange range{VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
        const VkClearColorValue zero{};
        for (auto* image : {&frame0, &frame1, &depth}) {
            image->barrier(init, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, 1);
            vkCmdClearColorImage(init, image->image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, &zero, 1, &range);
            image->barrier(init, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_GENERAL, 1, 1);
        }

        VkImageViewCreateInfo vi{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};
        vi.image = draw.image;
        vi.format = VK_FORMAT_R32G32_UINT;
        vi.viewType = VK_IMAGE_VIEW_TYPE_2D;
        vi.components = {VK_COMPONENT_SWIZZLE_R, VK_COMPONENT_SWIZZLE_G,
                         VK_COMPONENT_SWIZZLE_ZERO, VK_COMPONENT_SWIZZLE_ONE};
        vi.subresourceRange = range;
        check(vkCreateImageView(c.device, &vi, nullptr, &current));
        VkSamplerCreateInfo sci{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};
        sci.magFilter = sci.minFilter = VK_FILTER_LINEAR;
        sci.addressModeU = sci.addressModeV = sci.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        check(vkCreateSampler(c.device, &sci, nullptr, &sample));
        constexpr std::array types = {VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,
            VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE, VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE,
            VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE, VK_DESCRIPTOR_TYPE_SAMPLER};
        VkDescriptorSetLayoutBinding bindings[types.size()]{};
        for (uint32_t i = 0; i < types.size(); ++i)
            bindings[i] = {i, types[i], 1, VK_SHADER_STAGE_COMPUTE_BIT, nullptr};
        VkDescriptorSetLayoutCreateInfo dsl{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
        dsl.bindingCount = uint32_t(types.size());
        dsl.pBindings = bindings;
        check(vkCreateDescriptorSetLayout(c.device, &dsl, nullptr, &set_layout));
        const VkDescriptorPoolSize sizes[] = {{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 2},
            {VK_DESCRIPTOR_TYPE_STORAGE_IMAGE, 2}, {VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE, 6},
            {VK_DESCRIPTOR_TYPE_SAMPLER, 2}};
        VkDescriptorPoolCreateInfo dpi{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
        dpi.maxSets = 2;
        dpi.poolSizeCount = 4;
        dpi.pPoolSizes = sizes;
        check(vkCreateDescriptorPool(c.device, &dpi, nullptr, &pool));
        const VkDescriptorSetLayout layouts[] = {set_layout, set_layout};
        VkDescriptorSetAllocateInfo da{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
        da.descriptorPool = pool;
        da.descriptorSetCount = 2;
        da.pSetLayouts = layouts;
        check(vkAllocateDescriptorSets(c.device, &da, sets));
        const VkDescriptorBufferInfo constants{flat.handle, 0, 256};
        for (unsigned i = 0; i < 2; ++i) {
            const VkDescriptorImageInfo images[] = {
                {VK_NULL_HANDLE, i ? frame1.view : frame0.view, VK_IMAGE_LAYOUT_GENERAL},
                {VK_NULL_HANDLE, i ? frame0.view : frame1.view, VK_IMAGE_LAYOUT_GENERAL},
                {VK_NULL_HANDLE, current, VK_IMAGE_LAYOUT_GENERAL},
                {VK_NULL_HANDLE, depth.view, VK_IMAGE_LAYOUT_GENERAL},
                {sample, VK_NULL_HANDLE, VK_IMAGE_LAYOUT_UNDEFINED}};
            VkWriteDescriptorSet writes[types.size()]{};
            for (uint32_t binding = 0; binding < types.size(); ++binding) {
                auto& w = writes[binding];
                w = {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};
                w.dstSet = sets[i];
                w.dstBinding = binding;
                w.descriptorCount = 1;
                w.descriptorType = types[binding];
                if (binding == 0) w.pBufferInfo = &constants;
                else w.pImageInfo = &images[binding - 1];
            }
            vkUpdateDescriptorSets(c.device, uint32_t(types.size()), writes, 0, nullptr);
        }
        VkPushConstantRange pc{VK_SHADER_STAGE_COMPUTE_BIT, 0, 128};
        VkPipelineLayoutCreateInfo pli{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
        pli.setLayoutCount = pli.pushConstantRangeCount = 1;
        pli.pSetLayouts = &set_layout;
        pli.pPushConstantRanges = &pc;
        check(vkCreatePipelineLayout(c.device, &pli, nullptr, &layout));
        VkPipelineShaderStageRequiredSubgroupSizeCreateInfo sg{
            VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_REQUIRED_SUBGROUP_SIZE_CREATE_INFO};
        sg.requiredSubgroupSize = 32;
        auto module = load_module(c, live.shader);
        VkComputePipelineCreateInfo ci{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};
        ci.layout = layout;
        ci.stage = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
                    c.explicit_subgroup_stages & VK_SHADER_STAGE_COMPUTE_BIT ? &sg : nullptr, 0,
                    VK_SHADER_STAGE_COMPUTE_BIT, module, "main", nullptr};
        auto result = vkCreateComputePipelines(c.device, VK_NULL_HANDLE, 1, &ci, nullptr, &pipeline);
        vkDestroyShaderModule(c.device, module, nullptr);
        check(result);
    }

    void record(VkCommandBuffer cmd, const Buffer& destination, const VkBufferImageCopy& region,
                const void* live_constants) {
        // The previous submission has finished before the host changes this mapped buffer.
        constexpr size_t history_offset = 48 * sizeof(float);
        std::memcpy(static_cast<uint8_t*>(flat.data) + history_offset,
                    static_cast<const uint8_t*>(live_constants) + history_offset, sizeof(float));
        vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, pipeline);
        vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, layout, 0, 1, &sets[ping], 0, nullptr);
        vkCmdPushConstants(cmd, layout, VK_SHADER_STAGE_COMPUTE_BIT, 0, 128, push);
        vkCmdDispatch(cmd, extent.width / 8, extent.height / 8, 1);
        auto& output = ping ? frame1 : frame0;
        output.barrier(cmd, VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, 1, 1);
        vkCmdCopyImageToBuffer(cmd, output.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                               destination.handle, 1, &region);
        output.barrier(cmd, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_IMAGE_LAYOUT_GENERAL, 1, 1);
        ping ^= 1;
    }

    ~TemporalResolve() {
        auto d = context.device;
        vkDestroyPipeline(d, pipeline, nullptr);
        vkDestroyPipelineLayout(d, layout, nullptr);
        vkDestroyDescriptorPool(d, pool, nullptr);
        vkDestroyDescriptorSetLayout(d, set_layout, nullptr);
        vkDestroySampler(d, sample, nullptr);
        vkDestroyImageView(d, current, nullptr);
    }

    static constexpr auto frame_usage = VK_IMAGE_USAGE_STORAGE_BIT | VK_IMAGE_USAGE_SAMPLED_BIT |
        VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT;
};

static void draw(Context& c, const char* vs, const char* ps, const char* fleck,
                 const char* noise_file, const char* particle_file, const char* view_file,
                 const char* output, const LiveFrames* live = nullptr) {
    const VkExtent2D extent = live ? VkExtent2D{176, 256} : VkExtent2D{512, 512};
    const auto [width, height] = extent;
    const auto pixel_count = width * height;
    constexpr uint32_t layers = 128;
    constexpr uint32_t mips = 8;
    constexpr auto sampled = VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT;
    // Two regions: face/body records and the separately drawn antenna mesh.
    // Special appearances contain more strokes than the original single-Imp fixture.
    constexpr unsigned capacity = 16384;
    const auto particle_bytes = live ? std::vector<uint8_t>{} : read(particle_file);
    require(live || (particle_bytes.size() % 136 == 0 && !particle_bytes.empty()), "invalid particles");
    Buffer particles(c, live ? capacity * 136 : particle_bytes.size());
    if (!live) std::memcpy(particles.data, particle_bytes.data(), particle_bytes.size());
    Buffer readback(c, pixel_count * 8);
    Buffer vflat(c, 300), pflat(c, 336), stick_flat(c, 328), stick_path(c, 4096),
           planes(c, 256), pagetable(c, 256), fault(c, 256), stick_fault(c, 256),
           eye_flat(c, 300), eye_fault(c, 256);
    const auto view_bytes = read(view_file);
    require(view_bytes.size() == 208, "invalid Imp view state");
    Buffer matrix(c, 16384), lights(c, 256), view(c, view_bytes), anatomy(c, 4096);
    *static_cast<uint64_t*>(pagetable.data) = matrix.address;
    auto* vf = static_cast<float*>(vflat.data);
    for (auto i : {28, 32, 36, 40, 52, 58, 62, 66, 70}) vf[i] = 1;
    vf[57] = vf[65] = 2;
    auto* pf = static_cast<float*>(pflat.data);
    pf[72] = pf[78] = 1;
    if (live) {
        std::memcpy(pflat.data, live->draw_constants, 336);
        std::memcpy(anatomy.data, live->light_parameters, 200);
        std::memcpy(stick_flat.data, live->stick_constants, 328);
        std::memcpy(vflat.data, live->vertex_constants, 300);
        std::memcpy(eye_flat.data, live->eye_constants, 300);
        for (auto* flat : {&vflat, &eye_flat}) {
            auto* u = static_cast<uint32_t*>(flat->data);
            auto* f = static_cast<float*>(flat->data);
            u[24] = 0;
            u[54] = 0;
            for (auto index : {25, 26, 27, 33, 34, 35}) f[index] = 0.0f;
            f[28] = f[36] = 1.0f;
            f[57] = f[65] = 2.0f;
            f[58] = f[62] = f[66] = f[70] = 1.0f;
        }
        auto* stick = static_cast<uint32_t*>(stick_flat.data);
        stick[28] = capacity / 2;
        auto* sf = static_cast<float*>(stick_flat.data);
        for (auto index : {31, 32, 33, 39, 40, 41}) sf[index] = 0.0f;
        sf[34] = sf[42] = 1.0f;
        // The stick stores the camera Z at 60 and 68. 63 and 71
        // are quaternion components, so changing them splits the stick from its flecks.
        stick[57] = 0;
        sf[60] = sf[68] = 2.0f;
    }
    auto* state = static_cast<float*>(view.data);
    if (!live) {
        state[0] = state[1] = width / 2.0f;
        state[3] = pixel_count;
    }
    auto* projection = static_cast<float*>(matrix.data) + 85;
    // Add transparent space around the original 160-pixel projection.
    projection[0] = live ? 0.49f * 160 / width : 0.85f;
    projection[5] = live ? -0.49f * 160 / height : -0.85f;
    projection[10] = live ? 0.20f : 0.25f;
    projection[13] = live ? 0.32f * 160 / height : 0.0f;
    projection[14] = live ? 0.10f : 0.0f;
    projection[15] = 1.0f;

    const auto dds = read(fleck);
    const auto noise_bytes = read(noise_file);
    require(dds.size() == 5593236 && noise_bytes.size() == 128 * 128, "invalid texture data");
    Buffer fleck_src(c, std::vector<uint8_t>(dds.begin() + 148, dds.end()));
    Buffer noise_src(c, noise_bytes);
    DrawImage flecks(c, 256, 256, layers, mips, VK_FORMAT_BC4_UNORM_BLOCK, sampled);
    DrawImage noise(c, 128, 128, 1, 1, VK_FORMAT_R8_UNORM, sampled);
    constexpr auto output_format = VK_FORMAT_R32G32_UINT;
    DrawImage target(c, width, height, 1, 1, output_format,
                     VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT |
                     VK_IMAGE_USAGE_SAMPLED_BIT);
    constexpr auto depth_format = VK_FORMAT_D32_SFLOAT;
    DrawImage depth(c, width, height, 1, 1, depth_format, VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT);
    std::vector<VkBufferImageCopy> copies;
    VkDeviceSize texture_offset = 0;
    for (uint32_t layer = 0; layer < layers; ++layer) {
        for (uint32_t mip = 0; mip < mips; ++mip) {
            const uint32_t size = 256 >> mip;
            VkBufferImageCopy copy{};
            copy.bufferOffset = texture_offset;
            copy.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, mip, layer, 1};
            copy.imageExtent = {size, size, 1};
            copies.push_back(copy);
            const uint32_t blocks = (size + 3) / 4;
            texture_offset += blocks * blocks * 8;
        }
    }
    require(texture_offset == dds.size() - 148, "invalid DDS slice layout");
    VkBufferImageCopy noise_copy{};
    noise_copy.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    noise_copy.imageExtent = {128, 128, 1};
    c.begin(0);
    const auto cmd = c.commands[0];
    flecks.barrier(cmd, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, layers, mips);
    noise.barrier(cmd, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, 1);
    vkCmdCopyBufferToImage(cmd, fleck_src.handle, flecks.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                           uint32_t(copies.size()), copies.data());
    vkCmdCopyBufferToImage(cmd, noise_src.handle, noise.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                           1, &noise_copy);
    flecks.barrier(cmd, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
                   layers, mips);
    noise.barrier(cmd, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
                  1, 1);
    VkSamplerCreateInfo sci{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};
    sci.magFilter = sci.minFilter = VK_FILTER_LINEAR;
    sci.mipmapMode = VK_SAMPLER_MIPMAP_MODE_LINEAR;
    sci.addressModeU = sci.addressModeV = sci.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sci.maxLod = float(mips - 1);
    VkSampler smp{};
    check(vkCreateSampler(c.device, &sci, nullptr, &smp));

    std::array<VkDescriptorSetLayoutBinding, 20> bindings{};
    std::array<VkWriteDescriptorSet, 20> writes{};
    std::array<VkDescriptorBufferInfo, 20> buffers{};
    std::array<VkDescriptorImageInfo, 20> images{};
    Buffer* const buf[] = {&lights, &view, &anatomy, &pflat, nullptr, nullptr, nullptr, nullptr,
                           nullptr, nullptr, &particles, &planes, &vflat, &pagetable, &fault,
                           &stick_path, &stick_flat, &stick_fault, &eye_flat, &eye_fault};
    for (uint32_t i = 0; i < bindings.size(); ++i) {
        const auto type = buf[i] ? VK_DESCRIPTOR_TYPE_STORAGE_BUFFER : i < 8 ?
                                  VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE : VK_DESCRIPTOR_TYPE_SAMPLER;
        const VkShaderStageFlags stage = i < 10 ? VK_SHADER_STAGE_FRAGMENT_BIT : VK_SHADER_STAGE_VERTEX_BIT;
        bindings[i] = {i, type, 1, stage, nullptr};
        auto& w = writes[i];
        w.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        w.dstBinding = i;
        w.descriptorCount = 1;
        w.descriptorType = type;
        if (buf[i]) {
            buffers[i] = {buf[i]->handle, 0, VK_WHOLE_SIZE};
            w.pBufferInfo = &buffers[i];
        } else {
            images[i] = {i >= 8 ? smp : VK_NULL_HANDLE, i == 7 ? flecks.view : noise.view,
                         VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
            w.pImageInfo = &images[i];
        }
    }
    VkDescriptorSetLayoutCreateInfo dsl{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
    dsl.bindingCount = uint32_t(bindings.size());
    dsl.pBindings = bindings.data();
    VkDescriptorSetLayout set_layout{};
    check(vkCreateDescriptorSetLayout(c.device, &dsl, nullptr, &set_layout));
    const VkDescriptorPoolSize sizes[] = {{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 14},
        {VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE, 4}, {VK_DESCRIPTOR_TYPE_SAMPLER, 2}};
    VkDescriptorPoolCreateInfo dpi{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
    dpi.maxSets = 1;
    dpi.poolSizeCount = 3;
    dpi.pPoolSizes = sizes;
    VkDescriptorPool pool{};
    check(vkCreateDescriptorPool(c.device, &dpi, nullptr, &pool));
    VkDescriptorSetAllocateInfo da{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
    da.descriptorPool = pool;
    da.descriptorSetCount = 1;
    da.pSetLayouts = &set_layout;
    VkDescriptorSet set{};
    check(vkAllocateDescriptorSets(c.device, &da, &set));
    for (auto& w : writes) w.dstSet = set;
    vkUpdateDescriptorSets(c.device, uint32_t(writes.size()), writes.data(), 0, nullptr);

    constexpr VkShaderStageFlags stages = VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT;
    VkPushConstantRange range{stages, 0, 128};
    VkPipelineLayoutCreateInfo pli{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
    pli.setLayoutCount = pli.pushConstantRangeCount = 1;
    pli.pSetLayouts = &set_layout;
    pli.pPushConstantRanges = &range;
    VkPipelineLayout layout{};
    check(vkCreatePipelineLayout(c.device, &pli, nullptr, &layout));
    VkPipelineShaderStageRequiredSubgroupSizeCreateInfo sg{
        VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_REQUIRED_SUBGROUP_SIZE_CREATE_INFO};
    sg.requiredSubgroupSize = 32;
    VkPipelineShaderStageCreateInfo shaders[2]{};
    shaders[0] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0,
                  VK_SHADER_STAGE_VERTEX_BIT, load_module(c, vs), "main", nullptr};
    shaders[1] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
                  c.explicit_subgroup_stages & VK_SHADER_STAGE_FRAGMENT_BIT ? &sg : nullptr, 0,
                  VK_SHADER_STAGE_FRAGMENT_BIT, load_module(c, ps), "main", nullptr};
    VkPipelineVertexInputStateCreateInfo vi{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
    VkPipelineInputAssemblyStateCreateInfo ia{VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};
    ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_STRIP;
    VkViewport vp{0, 0, float(width), float(height), 0, 1};
    VkRect2D sc{{0, 0}, extent};
    VkPipelineViewportStateCreateInfo vsi{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};
    vsi.viewportCount = vsi.scissorCount = 1;
    vsi.pViewports = &vp;
    vsi.pScissors = &sc;
    VkPipelineRasterizationStateCreateInfo rs{VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};
    rs.lineWidth = 1.0f;
    VkPipelineMultisampleStateCreateInfo ms{VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
    VkPipelineColorBlendAttachmentState attachment{};
    attachment.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT;
    VkPipelineColorBlendStateCreateInfo blend{VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};
    blend.attachmentCount = 1;
    blend.pAttachments = &attachment;
    VkPipelineRenderingCreateInfo rendering{VK_STRUCTURE_TYPE_PIPELINE_RENDERING_CREATE_INFO};
    rendering.colorAttachmentCount = 1;
    rendering.pColorAttachmentFormats = &output_format;
    rendering.depthAttachmentFormat = depth_format;
    VkPipelineDepthStencilStateCreateInfo depth_state{VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO};
    depth_state.depthTestEnable = VK_TRUE;
    depth_state.depthWriteEnable = VK_TRUE;
    depth_state.depthCompareOp = VK_COMPARE_OP_GREATER_OR_EQUAL;
    VkGraphicsPipelineCreateInfo pi{VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO};
    pi.pNext = &rendering;
    pi.stageCount = 2;
    pi.pStages = shaders;
    pi.pVertexInputState = &vi;
    pi.pInputAssemblyState = &ia;
    pi.pViewportState = &vsi;
    pi.pRasterizationState = &rs;
    pi.pMultisampleState = &ms;
    pi.pDepthStencilState = &depth_state;
    pi.pColorBlendState = &blend;
    pi.layout = layout;
    VkPipeline pipeline{};
    check(vkCreateGraphicsPipelines(c.device, VK_NULL_HANDLE, 1, &pi, nullptr, &pipeline));
    VkPipeline stick_pipeline{}, eye_pipeline{};
    if (live) {
        const auto body_vertex = shaders[0].module;
        auto vertex_pipeline = [&](const char* shader, VkPipeline& result) {
            shaders[0].module = load_module(c, shader);
            const auto status = vkCreateGraphicsPipelines(c.device, VK_NULL_HANDLE, 1, &pi, nullptr, &result);
            vkDestroyShaderModule(c.device, shaders[0].module, nullptr);
            check(status);
        };
        vertex_pipeline(live->stick_shader, stick_pipeline);
        vertex_pipeline(live->eye_shader, eye_pipeline);
        shaders[0].module = body_vertex;
    }
    require(sync_errors + other_errors == 0, "graphics pipeline validation failed");

    std::unique_ptr<TemporalResolve> temporal;
    if (live) {
        temporal = std::make_unique<TemporalResolve>(c, extent, target, *live, cmd);
        check(vkEndCommandBuffer(cmd));
        c.submit(0, 1, true);
    }
    VkRenderingAttachmentInfo color{VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_INFO};
    color.imageView = target.view;
    color.imageLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
    color.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    color.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
    VkRenderingInfo ri{VK_STRUCTURE_TYPE_RENDERING_INFO};
    ri.renderArea = sc;
    ri.layerCount = ri.colorAttachmentCount = 1;
    ri.pColorAttachments = &color;
    VkRenderingAttachmentInfo depth_attachment{VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_INFO};
    depth_attachment.imageView = depth.view;
    depth_attachment.imageLayout = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;
    depth_attachment.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    depth_attachment.storeOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    depth_attachment.clearValue.depthStencil = {0.0f, 0};
    ri.pDepthAttachment = &depth_attachment;
    std::array<uint32_t, 32> push{};
    VkBufferImageCopy copy{};
    copy.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    copy.imageExtent = {width, height, 1};
    auto previous = VK_IMAGE_LAYOUT_UNDEFINED;
    do {
        const int count = live ? live->next(particles.data, capacity/2, live->user) : int(particle_bytes.size()/136);
        if (count == 0) break;
        if (live && live->appearance_rgb) std::memcpy(static_cast<uint8_t*>(view.data) + 16, live->appearance_rgb, 12);
        require(count > 0 && (!live || count <= int(capacity)), "invalid particle count from host");
        int sticks = 0, eyes = 0;
        if (live) {
            sticks = live->stick(static_cast<uint8_t*>(particles.data) + (capacity/2)*136,
                                 capacity/2, stick_path.data, live->user);
            require(sticks >= 0 && sticks <= int(capacity/2), "invalid antenna record count");
            std::memcpy(anatomy.data, stick_path.data, 4096);
            static_cast<uint32_t*>(stick_flat.data)[29] = uint32_t(sticks + capacity/2);
            eyes = live->eyes(live->user);
            require(eyes >= 0 && eyes < count, "invalid eye record count");
            auto* body_vertex = static_cast<float*>(vflat.data);
            body_vertex[49] = body_vertex[50];
            body_vertex[50] += 1.0f / 30;
            c.begin(0);
        }
        target.barrier(cmd, previous, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, 1, 1);
        depth.barrier(cmd, previous == VK_IMAGE_LAYOUT_UNDEFINED ? VK_IMAGE_LAYOUT_UNDEFINED :
            VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL, 1, 1);
        vkCmdBeginRendering(cmd, &ri);
        vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline);
        vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, layout, 0, 1, &set, 0, nullptr);
        vkCmdPushConstants(cmd, layout, stages, 0, uint32_t(push.size() * sizeof(uint32_t)), push.data());
        vkCmdDraw(cmd, 4, uint32_t(count - eyes), 0, 0);
        if (sticks) {
            vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, stick_pipeline);
            vkCmdDraw(cmd, 4, uint32_t(sticks), 0, 0);
        }
        if (eyes) {
            vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, eye_pipeline);
            vkCmdDraw(cmd, 4, uint32_t(eyes), 0, uint32_t(count - eyes));
        }
        vkCmdEndRendering(cmd);
        previous = live ? VK_IMAGE_LAYOUT_GENERAL : VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
        target.barrier(cmd, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, previous, 1, 1);
        if (temporal) temporal->record(cmd, readback, copy, live->constants);
        else vkCmdCopyImageToBuffer(cmd, target.image, previous, readback.handle, 1, &copy);
        VkMemoryBarrier host{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
        host.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
        host.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
        vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT,
                             0, 1, &host, 0, nullptr, 0, nullptr);
        check(vkEndCommandBuffer(cmd));
        c.submit(0, 1, true);
        require(sync_errors + other_errors == 0, "frame validation failed");
        if (live) {
            if (!live->present(readback.data, width, height, live->user)) break;
        } else {
            const auto* result = static_cast<const uint64_t*>(readback.data);
            const auto covered = std::count_if(result, result + pixel_count, [](auto p) { return p != 0; });
            std::ofstream(output, std::ios::binary).write(reinterpret_cast<const char*>(result), pixel_count * 8);
            std::cout << "original shader coverage=" << covered << " / " << pixel_count << '\n';
            require(covered > 0, "original shaders emitted no Imp pixels");
        }
    } while (live);
    vkDestroyPipeline(c.device, pipeline, nullptr);
    if (stick_pipeline) vkDestroyPipeline(c.device, stick_pipeline, nullptr);
    if (eye_pipeline) vkDestroyPipeline(c.device, eye_pipeline, nullptr);
    for (auto& shader : shaders) vkDestroyShaderModule(c.device, shader.module, nullptr);
    vkDestroyPipelineLayout(c.device, layout, nullptr);
    vkDestroyDescriptorPool(c.device, pool, nullptr);
    vkDestroyDescriptorSetLayout(c.device, set_layout, nullptr);
    vkDestroySampler(c.device, smp, nullptr);
}

extern "C" __declspec(dllexport) int imp_render_loop(
    const char* vs, const char* ps, const char* fleck, const char* noise, const char* view,
    const LiveFrames* frames, char* error, size_t error_size) {
    try {
        Context ctx(false);
        draw(ctx, vs, ps, fleck, noise, nullptr, view, nullptr, frames);
        return 0;
    } catch (const std::exception& ex) {
        if (error_size) strncpy_s(error, error_size, ex.what(), _TRUNCATE);
        return 1;
    }
}

extern "C" __declspec(dllexport) void imp_decode_bgra(
    const uint16_t* source, uint8_t* destination, unsigned count) {
    // Dreams DoPost (c77d5c09), SDR tone mapping with the game exposure at 1.
    auto display = [](float linear) {
        const float x = std::max(0.0f, linear - 0.004f);
        return uint8_t(std::lround(255.0f * x * (6.2f*x + 0.5f) /
                                  std::fma(x, std::fma(6.2f, x, 1.7f), 0.06f)));
    };
    for (unsigned i = 0; i < count; ++i, source += 4, destination += 4) {
        auto a = _cvtsh_ss(source[3]);
        if (!(a > 0.0f) || !std::isfinite(a)) {
            std::memset(destination, 0, 4);
            continue;
        }
        const auto y = _cvtsh_ss(source[0]), co = _cvtsh_ss(source[1]), cg = _cvtsh_ss(source[2]);
        if (!std::isfinite(y) || !std::isfinite(co) || !std::isfinite(cg)) {
            std::memset(destination, 0, 4);
            continue;
        }
        // UIComp (5e949cd5) expands the premultiplied Imp layer before DoPost.
        const float scale = 1.0f/std::max(1.0f-std::abs(y), 0.0001f);
        destination[0] = display((y-co-cg)*scale);
        destination[1] = display((y+cg)*scale);
        destination[2] = display((y+co-cg)*scale);
        // Windows requires premultiplied BGRA. Keep the native display RGB
        // over black even when its tone-mapped emissive value exceeds alpha.
        destination[3] = std::max({destination[0], destination[1], destination[2],
                                   uint8_t(std::lround(255.0f*std::min(a, 1.0f)))});
    }
}

namespace {
struct BloomImage {
    unsigned width{}, height{};
    std::vector<__m128> pixels;

    void resize(unsigned w, unsigned h) {
        width = w;
        height = h;
        pixels.resize(size_t{w} * h);
    }

    __m128 at(int x, int y) const {
        if (static_cast<unsigned>(x) >= width || static_cast<unsigned>(y) >= height)
            return _mm_setzero_ps();
        return pixels[size_t{static_cast<unsigned>(y)} * width + x];
    }

    __m128 sample(int x, int y, __m128 fx, __m128 fy, bool interior = false) const {
        __m128 a, b, c, d;
        if (interior) {
            const auto* row = pixels.data() + size_t{static_cast<unsigned>(y)} * width + x;
            a = row[0]; b = row[1]; c = row[width]; d = row[width + 1];
        } else {
            a = at(x, y); b = at(x + 1, y); c = at(x, y + 1); d = at(x + 1, y + 1);
        }
        const auto top = _mm_fmadd_ps(_mm_sub_ps(b, a), fx, a);
        const auto bottom = _mm_fmadd_ps(_mm_sub_ps(d, c), fx, c);
        return _mm_fmadd_ps(_mm_sub_ps(bottom, top), fy, top);
    }
};

__m128 half_storage(__m128 pixel) {
    return _mm_cvtph_ps(_mm_cvtps_ph(pixel, _MM_FROUND_TO_NEAREST_INT));
}

struct BloomRect { int left, top, right, bottom; };

void bloom_down(const BloomImage& in, BloomImage& out, bool first, BloomRect bounds) {
    // BloomPyramid_DownSample (716342fc), texel-center offsets from the shader.
    constexpr std::array<std::array<float, 2>, 9> taps{{
        {1, 1}, {2.8276150227f, 1.8122950792f}, {1.7179396152f, 2.8666982651f},
        {0.1877046824f, 2.8276147842f}, {-0.8666983843f, 1.7179393768f},
        {-0.8276150227f, 0.1877050400f}, {0.2820599675f, -0.8666981459f},
        {1.8122951984f, -0.8276149035f}, {2.8666982651f, 0.2820602655f},
    }};
    struct Tap { int x, y; float fx, fy; };
    constexpr auto samples = [=] {
        std::array<Tap, taps.size()> result{};
        for (size_t i = 0; i < taps.size(); ++i) {
            const float x = taps[i][0] - 0.5f, y = taps[i][1] - 0.5f;
            const auto floor = [](float value) {
                const int integer = static_cast<int>(value);
                return integer - (value < integer);
            };
            const int tx = floor(x), ty = floor(y);
            result[i] = {tx, ty, x - tx, y - ty};
        }
        return result;
    }();
    const auto weight = _mm_set1_ps(first ? 0.0032f : 0.1f);
    const auto bias = _mm_set1_ps(first ? -0.0024f : 0.0f);
    int left = 0, top = 0, right = static_cast<int>(out.width), bottom = static_cast<int>(out.height);
    if (first) {
        // No source texel outside the particle bounds can contribute to the nine taps.
        std::fill(out.pixels.begin(), out.pixels.end(), _mm_setzero_ps());
        left = std::max(0, (bounds.left - 2) / 2);
        top = std::max(0, (bounds.top - 2) / 2);
        right = std::min(right, (bounds.right + 2) / 2 + 1);
        bottom = std::min(bottom, (bounds.bottom + 2) / 2 + 1);
    }
    for (int y = top; y < bottom; ++y) {
        const bool inner_row = y >= 1 && 2 * y + 3 < static_cast<int>(in.height);
        for (int x = left; x < right; ++x) {
            auto sum = _mm_setzero_ps();
            const bool interior = inner_row && x >= 1 && 2 * x + 3 < static_cast<int>(in.width);
            for (const auto& [tx, ty, fx, fy] : samples) {
                sum = _mm_add_ps(sum, in.sample(2 * x + tx, 2 * y + ty,
                                                _mm_set1_ps(fx), _mm_set1_ps(fy), interior));
            }
            const auto filtered = _mm_add_ps(_mm_mul_ps(sum, weight), bias);
            const auto positive = _mm_max_ps(filtered, _mm_setzero_ps());
            out.pixels[static_cast<size_t>(y) * out.width + x] =
                half_storage(_mm_blend_ps(positive, _mm_setzero_ps(), 8));
        }
    }
}

void bloom_up(const BloomImage& in, BloomImage& out) {
    // BloomPyramid_UpSample (11b0ece9), additive bloom component.
    for (unsigned y = 0; y < out.height; ++y) {
        const int ty = (static_cast<int>(y) + 1) / 2 - 1;
        const auto fy = _mm_set1_ps((y & 1) ? 0.25f : 0.75f);
        for (unsigned x = 0; x < out.width; ++x) {
            const int tx = (static_cast<int>(x) + 1) / 2 - 1;
            const auto fx = _mm_set1_ps((x & 1) ? 0.25f : 0.75f);
            auto& pixel = out.pixels[size_t{y} * out.width + x];
            pixel = half_storage(_mm_add_ps(pixel, in.sample(tx, ty, fx, fy)));
        }
    }
}
} // namespace

extern "C" __declspec(dllexport) void imp_decode_cursor_bgra(
    const uint16_t* source, uint8_t* destination, unsigned width, unsigned height) {
    // The captured 1920x1080 UI chain reduces eight times (ending at 8x5).
    thread_local std::array<BloomImage, 9> pyramid;
    pyramid.front().resize(width, height);
    auto& image = pyramid.front().pixels;
    BloomRect bounds{static_cast<int>(width), static_cast<int>(height), -1, -1};
    for (size_t i = 0; i < image.size(); ++i) {
        const auto* pixel = source + 4 * i;
        const float y = _cvtsh_ss(pixel[0]), co = _cvtsh_ss(pixel[1]), cg = _cvtsh_ss(pixel[2]);
        const float a = _cvtsh_ss(pixel[3]);
        if (!(a > 0.0f) || !std::isfinite(a) || !std::isfinite(y) ||
            !std::isfinite(co) || !std::isfinite(cg)) {
            image[i] = _mm_setzero_ps();
            continue;
        }
        const float scale = 1.0f / std::max(1.0f - std::abs(y), 0.0001f);
        image[i] = half_storage(_mm_setr_ps((y - co - cg) * scale, (y + cg) * scale,
                                           (y + co - cg) * scale, a));
        const int column = static_cast<int>(i % width), row = static_cast<int>(i / width);
        bounds.left = std::min(bounds.left, column);
        bounds.top = std::min(bounds.top, row);
        bounds.right = std::max(bounds.right, column);
        bounds.bottom = std::max(bounds.bottom, row);
    }
    for (size_t level = 1; level < pyramid.size(); ++level) {
        const auto& previous = pyramid[level - 1];
        auto& current = pyramid[level];
        current.resize((previous.width + 1) / 2, (previous.height + 1) / 2);
        bloom_down(previous, current, level == 1, bounds);
    }
    for (size_t level = pyramid.size() - 1; level > 0; --level)
        bloom_up(pyramid[level], pyramid[level - 1]);
    for (size_t i = 0; i < image.size(); ++i, destination += 4) {
        // DoPost (c77d5c09) after the additive bloom, in the original SDR colour curve.
        const auto x = _mm_max_ps(_mm_sub_ps(image[i], _mm_set1_ps(0.004f)), _mm_setzero_ps());
        const auto num = _mm_mul_ps(_mm_mul_ps(_mm_set1_ps(255), x),
                                    _mm_add_ps(_mm_mul_ps(_mm_set1_ps(6.2f), x), _mm_set1_ps(0.5f)));
        const auto den = _mm_fmadd_ps(x, _mm_fmadd_ps(_mm_set1_ps(6.2f), x, _mm_set1_ps(1.7f)),
                                     _mm_set1_ps(0.06f));
        const auto alpha = _mm_mul_ps(_mm_min_ps(image[i], _mm_set1_ps(1)), _mm_set1_ps(255));
        const auto values = _mm_blend_ps(_mm_div_ps(num, den), alpha, 8);
        const auto ints = _mm_cvttps_epi32(_mm_add_ps(values, _mm_set1_ps(0.5f)));
        const auto words = _mm_packus_epi32(ints, ints);
        const auto packed = _mm_cvtsi128_si32(_mm_packus_epi16(words, words));
        std::memcpy(destination, &packed, 4);
        // The transparent Windows overlay carries the halo beyond the particle alpha.
        destination[3] = std::max({destination[0], destination[1], destination[2], destination[3]});
    }
}

extern "C" __declspec(dllexport) bool imp_interactive_at(LONG x, LONG y, RECT* bounds) {
    using Microsoft::WRL::ComPtr;
    struct HoverReader {
        HRESULT initialized = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
        ComPtr<IUIAutomation> automation;
        ComPtr<IUIAutomationTreeWalker> walker;
        ComPtr<IUIAutomationCacheRequest> cache;
        HoverReader() {
            if (SUCCEEDED(initialized) && SUCCEEDED(CoCreateInstance(__uuidof(CUIAutomation),
                    nullptr, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&automation))) &&
                SUCCEEDED(automation->get_ControlViewWalker(&walker)) &&
                SUCCEEDED(automation->CreateCacheRequest(&cache))) {
                for (const auto id : {UIA_IsEnabledPropertyId, UIA_IsOffscreenPropertyId,
                                      UIA_ControlTypePropertyId, UIA_BoundingRectanglePropertyId}) {
                    if (FAILED(cache->AddProperty(id))) { cache.Reset(); break; }
                }
            }
        }
        ~HoverReader() {
            cache.Reset();
            walker.Reset();
            automation.Reset();
            if (SUCCEEDED(initialized)) CoUninitialize();
        }
    };
    thread_local HoverReader reader;
    const POINT point{x, y};
    ComPtr<IUIAutomationElement> element;
    if (!reader.cache || FAILED(reader.automation->ElementFromPointBuildCache(point,
                                reader.cache.Get(), &element)))
        return false;
    for (int level = 0; element && level < 6; ++level) {
        BOOL enabled{}, offscreen{};
        int type{};
        if (FAILED(element->get_CachedIsEnabled(&enabled)) || !enabled ||
            FAILED(element->get_CachedIsOffscreen(&offscreen)) || offscreen ||
            FAILED(element->get_CachedControlType(&type)))
            return false;
        switch (type) {
        case UIA_ButtonControlTypeId: case UIA_CheckBoxControlTypeId:
        case UIA_ComboBoxControlTypeId: case UIA_EditControlTypeId:
        case UIA_HyperlinkControlTypeId: case UIA_ListItemControlTypeId:
        case UIA_MenuItemControlTypeId: case UIA_RadioButtonControlTypeId:
        case UIA_ScrollBarControlTypeId: case UIA_SliderControlTypeId:
        case UIA_SpinnerControlTypeId: case UIA_SplitButtonControlTypeId:
        case UIA_TabItemControlTypeId: case UIA_ThumbControlTypeId:
        case UIA_TreeItemControlTypeId:
            return SUCCEEDED(element->get_CachedBoundingRectangle(bounds)) && PtInRect(bounds, point);
        case UIA_CustomControlTypeId: case UIA_DataItemControlTypeId: {
            ComPtr<IUnknown> action;
            if (SUCCEEDED(element->GetCurrentPattern(UIA_InvokePatternId, &action)) && action)
                return SUCCEEDED(element->get_CachedBoundingRectangle(bounds)) && PtInRect(bounds, point);
            break;
        }
        case UIA_WindowControlTypeId: case UIA_PaneControlTypeId:
        case UIA_DocumentControlTypeId: case UIA_TitleBarControlTypeId:
            return false;
        default:
            break;
        }
        ComPtr<IUIAutomationElement> parent;
        if (FAILED(reader.walker->GetParentElementBuildCache(element.Get(), reader.cache.Get(), &parent)))
            return false;
        element = std::move(parent);
    }
    return false;
}

int main(int argc, char** argv) {
    try {
        require(argc == 8, "expected: vertex fragment fleck-DDS noise particles view output");
        Context ctx(false);
        draw(ctx, argv[1], argv[2], argv[3], argv[4], argv[5], argv[6], argv[7]);
        return sync_errors + other_errors ? 2 : 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
