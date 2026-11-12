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
