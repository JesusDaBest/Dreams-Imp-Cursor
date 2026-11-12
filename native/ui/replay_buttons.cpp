// Replay captured Dreams UI inputs through their unchanged native shaders.
#include <vulkan/vulkan.h>
#include <filesystem>
#include <vector>
#include <stdexcept>
#include <cstring>
#include <io.h>
#include <fcntl.h>
#include <chrono>
#include <immintrin.h>
#include <cmath>
static bool ui_portable_device=false;
static VkResult create_ui_device(VkPhysicalDevice physical,const VkDeviceCreateInfo* info,const VkAllocationCallbacks* alloc,VkDevice* out){auto features=*info->pEnabledFeatures;features.independentBlend=VK_TRUE;auto copy=*info;copy.pEnabledFeatures=&features;
unsigned count=0;vkEnumerateDeviceExtensionProperties(physical,nullptr,&count,nullptr);std::vector<VkExtensionProperties> available(count);vkEnumerateDeviceExtensionProperties(physical,nullptr,&count,available.data());
bool found=false;for(auto e:available)if(std::strcmp(e.extensionName,"VK_AMD_shader_explicit_vertex_parameter")==0)found=true;if(!found&&!ui_portable_device)throw std::runtime_error("Native AMD interpolation extension not available for this offline replay");
std::vector<const char*> extensions(info->ppEnabledExtensionNames,info->ppEnabledExtensionNames+info->enabledExtensionCount);if(!ui_portable_device)extensions.push_back("VK_AMD_shader_explicit_vertex_parameter");copy.enabledExtensionCount=unsigned(extensions.size());copy.ppEnabledExtensionNames=extensions.data();return vkCreateDevice(physical,&copy,alloc,out);}
#define vkCreateDevice create_ui_device
#define main unused_compute_replay_main
#include "../tweak-menu-artifact/pause-image-replay/replay.cpp"
#undef main
#undef vkCreateDevice
#include "draw_image.h"
#include "native_post.h"
#include "native_bloom.h"

static std::ostream* ui_binary;
// Native render target is A2B10G10R10; Dreams VideoOut consumes the same
// stored bytes as A2R10G10B10 (vk_presenter.cpp). Decode that storage contract.
static void ui_videoout_rgba(const uint32_t* src,uint8_t* dst,size_t pixels){
 // Integer rounding is identical to the presenter's 10-bit UNORM conversion.
 auto u8=[](uint32_t x){return uint8_t((x*255+511)/1023);};
 size_t i=0;auto mask=_mm256_set1_epi32(1023);auto one=_mm256_set1_epi32(1);
 auto convert=[&](__m256i v){auto n=_mm256_add_epi32(_mm256_mullo_epi32(v,_mm256_set1_epi32(255)),_mm256_set1_epi32(511));return _mm256_srli_epi32(_mm256_add_epi32(_mm256_add_epi32(n,_mm256_srli_epi32(n,10)),one),10);};
 for(;i+8<=pixels;i+=8){auto x=_mm256_loadu_si256(reinterpret_cast<const __m256i*>(src+i));auto r=convert(_mm256_and_si256(_mm256_srli_epi32(x,20),mask));auto g=convert(_mm256_and_si256(_mm256_srli_epi32(x,10),mask));auto b=convert(_mm256_and_si256(x,mask));auto a=_mm256_mullo_epi32(_mm256_srli_epi32(x,30),_mm256_set1_epi32(85));a=_mm256_max_epi32(_mm256_max_epi32(r,g),_mm256_max_epi32(b,a));auto rgba=_mm256_or_si256(_mm256_or_si256(r,_mm256_slli_epi32(g,8)),_mm256_or_si256(_mm256_slli_epi32(b,16),_mm256_slli_epi32(a,24)));_mm256_storeu_si256(reinterpret_cast<__m256i*>(dst+i*4),rgba);}
 for(;i<pixels;++i){uint32_t x=src[i];auto* d=dst+i*4;d[0]=u8((x>>20)&1023);d[1]=u8((x>>10)&1023);d[2]=u8(x&1023);d[3]=std::max({d[0],d[1],d[2],uint8_t((x>>30)*85)});}
}

static void ui_display_rgba(const uint16_t* src,uint8_t* dst,size_t pixels){
    // Direct RGB UI layer -> Dreams DoPost c77d5c09 SDR curve. Unlike the
    // separate Imp layer, these UI shader outputs are not YCoCg encoded.
    auto display=[](float linear){float x=std::max(0.f,linear-.004f);return uint8_t(std::lround(255.f*x*(6.2f*x+.5f)/std::fma(x,std::fma(6.2f,x,1.7f),.06f)));};
    for(size_t i=0;i<pixels;++i,src+=4,dst+=4){float a=_cvtsh_ss(src[3]);if(!(a>0.f)||!std::isfinite(a)){std::memset(dst,0,4);continue;}
        float r=_cvtsh_ss(src[0]),g=_cvtsh_ss(src[1]),b=_cvtsh_ss(src[2]);if(!std::isfinite(r)||!std::isfinite(g)||!std::isfinite(b)){std::memset(dst,0,4);continue;}
        dst[0]=display(r);dst[1]=display(g);dst[2]=display(b);dst[3]=std::max({dst[0],dst[1],dst[2],uint8_t(std::lround(255.f*std::min(a,1.f)))});
    }
}
static void replay_ui(Context& c,const json& j) {
    const bool stream=j.value("stream",false);const bool has_post=j.contains("postprocess");const bool profile=j.value("profile",false)||j.value("validation",true);HANDLE output_mapping=nullptr;void* output_shared=nullptr;
    const bool display_rgba=j.value("display_rgba",false);const bool full_overlay=j.value("full_overlay",false);const size_t output_pixels=full_overlay?1920*1080:3*165*165;require(!has_post||(full_overlay&&display_rgba),"DoPost requires full RGBA overlay");
    if(j.contains("output_mapping")){auto name=j.at("output_mapping").get<std::string>();require(name.starts_with("Local\\DreamsImpUI-"),"Unexpected UI mapping name");output_mapping=OpenFileMappingA(FILE_MAP_WRITE,FALSE,name.c_str());require(output_mapping!=nullptr,"Native UI output mapping unavailable");output_shared=MapViewOfFile(output_mapping,FILE_MAP_WRITE,0,0,output_pixels*(display_rgba?4:8));require(output_shared!=nullptr,"Native UI output mapping too small");}
    const std::filesystem::path capture=j.at("capture").get<std::string>();
    auto path=[&](const char* name){return (capture/name).string();};
    auto geometry_bytes=read(path("stage-3-buffer0.bin"));
    if(j.contains("record_override")){auto record=read(j.at("record_override"));require(record.size()==524,"Original UI record must contain 524 bytes");auto push=read(path("push-data.bin"));unsigned index=0;std::memcpy(&index,push.data()+44,4);require((size_t(index)+1)*524<=geometry_bytes.size(),"Original UI record index outside captured buffer");std::memcpy(geometry_bytes.data()+size_t(index)*524,record.data(),524);}
    Buffer geometry(c,geometry_bytes);
    Buffer pf(c,read(path("stage-0-srt.bin"))),vf(c,read(path("stage-3-srt.bin")));
    Buffer planes(c,256),pages(c,8*1024*1024),faults(c,128*1024,true);
    constexpr unsigned width=1920,height=1080;
    DrawImage target(c,width,height,1,1,VK_FORMAT_R16G16B16A16_SFLOAT,
        VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT|VK_IMAGE_USAGE_TRANSFER_SRC_BIT|VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_STORAGE_BIT);
    DrawImage bloom(c,width,height,1,1,VK_FORMAT_R8_UNORM,
        VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT|VK_IMAGE_USAGE_TRANSFER_SRC_BIT);
    Buffer result(c,has_post?output_pixels*4:stream?output_pixels*8:width*height*8,true),bloom_result(c,width*height,true);
    std::vector<std::unique_ptr<DrawImage>> textures;
    for(const auto& t:j.at("textures")) {
        const unsigned w=t.at("width"),h=t.at("height"),layers=t.at("layers"),mips=t.at("mips");
        textures.push_back(std::make_unique<DrawImage>(c,w,h,layers,mips,VkFormat(int(t.at("format"))),
            VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT));
        auto& image=*textures.back();
        // Use the resource descriptor's actual channel swizzles.
        vkDestroyImageView(c.device,image.view,nullptr);
        VkImageViewCreateInfo vi{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};vi.image=image.image;
        vi.viewType=layers>1?VK_IMAGE_VIEW_TYPE_2D_ARRAY:VK_IMAGE_VIEW_TYPE_2D;
        vi.format=VkFormat(int(t.at("format")));vi.subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0,mips,0,layers};
        auto m=t.at("mapping");vi.components={VkComponentSwizzle(int(m[0])),VkComponentSwizzle(int(m[1])),VkComponentSwizzle(int(m[2])),VkComponentSwizzle(int(m[3]))};
        check(vkCreateImageView(c.device,&vi,nullptr,&image.view));
        std::vector<uint8_t> raw;std::vector<VkBufferImageCopy> copies;
        for(const auto& sub:t.at("subresources")) {
            auto bytes=read(sub.at("file"));unsigned mip=sub.at("mip"),layer=sub.at("layer");
            VkBufferImageCopy region{};region.bufferOffset=raw.size();
            region.imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,mip,layer,1};
            region.imageExtent={std::max(1u,w>>mip),std::max(1u,h>>mip),1};
            copies.push_back(region);raw.insert(raw.end(),bytes.begin(),bytes.end());
        }
        Buffer staging(c,raw);c.begin(0);auto cmd=c.commands[0];
        image.barrier(cmd,VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,layers,mips);
        vkCmdCopyBufferToImage(cmd,staging.handle,image.image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,unsigned(copies.size()),copies.data());
        image.barrier(cmd,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,layers,mips);
        check(vkEndCommandBuffer(cmd));c.submit(0,1,true);
    }
    std::vector<VkSampler> samplers;
    for(const auto& row:j.at("samplers")) {
        const auto& s=row.at("decoded");VkSamplerCreateInfo ci{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};
        ci.magFilter=VkFilter(int(s.at("mag")));ci.minFilter=VkFilter(int(s.at("min")));
        ci.mipmapMode=int(s.at("mip"))==2?VK_SAMPLER_MIPMAP_MODE_LINEAR:VK_SAMPLER_MIPMAP_MODE_NEAREST;
        auto clamp=[](int v){switch(v){case 0:return VK_SAMPLER_ADDRESS_MODE_REPEAT;case 2:return VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;case 6:return VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_BORDER;default:throw std::runtime_error("Uncaptured sampler address mode");}};
        ci.addressModeU=clamp(s.at("clamp_x"));ci.addressModeV=clamp(s.at("clamp_y"));ci.addressModeW=clamp(s.at("clamp_z"));
        ci.minLod=s.at("min_lod");ci.maxLod=s.at("max_lod");ci.mipLodBias=s.at("bias");
        ci.compareEnable=int(row.at("index"))==0;ci.compareOp=VkCompareOp(int(s.at("compare")));
        ci.borderColor=VK_BORDER_COLOR_FLOAT_TRANSPARENT_BLACK;VkSampler handle{};
        check(vkCreateSampler(c.device,&ci,nullptr,&handle));samplers.push_back(handle);
    }
    std::array<VkDescriptorSetLayoutBinding,18> bindings{};
    std::array<VkWriteDescriptorSet,18> writes{};
    std::array<VkDescriptorBufferInfo,18> buffers{};
    std::array<VkDescriptorImageInfo,18> images{};
    Buffer* buf[]={&geometry,&pf,&pages,&faults,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr,&geometry,&planes,&vf,&pages,&faults};
    for(unsigned i=0;i<bindings.size();++i) {
        auto type=buf[i]?VK_DESCRIPTOR_TYPE_STORAGE_BUFFER:i<9?VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE:VK_DESCRIPTOR_TYPE_SAMPLER;
        bindings[i]={i,type,1,VkShaderStageFlags(i<13?VK_SHADER_STAGE_FRAGMENT_BIT:VK_SHADER_STAGE_VERTEX_BIT),nullptr};
        auto& w=writes[i];w.sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;w.dstBinding=i;w.descriptorCount=1;w.descriptorType=type;
        if(buf[i]){buffers[i]={buf[i]->handle,0,VK_WHOLE_SIZE};w.pBufferInfo=&buffers[i];}
        else {images[i]={i>=9?samplers.at(i-9):VK_NULL_HANDLE,i>=6&&i<9?textures.at(i-6)->view:VK_NULL_HANDLE,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};w.pImageInfo=&images[i];}
    }
    VkDescriptorSetLayoutCreateInfo sl{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};sl.bindingCount=bindings.size();sl.pBindings=bindings.data();
    VkDescriptorSetLayout set_layout{};check(vkCreateDescriptorSetLayout(c.device,&sl,nullptr,&set_layout));
    VkDescriptorPoolSize pool_sizes[]={{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,9},{VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE,5},{VK_DESCRIPTOR_TYPE_SAMPLER,4}};
    VkDescriptorPoolCreateInfo pc{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};pc.maxSets=1;pc.poolSizeCount=3;pc.pPoolSizes=pool_sizes;
    VkDescriptorPool pool{};check(vkCreateDescriptorPool(c.device,&pc,nullptr,&pool));
    VkDescriptorSetAllocateInfo sa{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};sa.descriptorPool=pool;sa.descriptorSetCount=1;sa.pSetLayouts=&set_layout;
    VkDescriptorSet set{};check(vkAllocateDescriptorSets(c.device,&sa,&set));
    for(auto& w:writes)w.dstSet=set;vkUpdateDescriptorSets(c.device,writes.size(),writes.data(),0,nullptr);
    constexpr auto stages=VK_SHADER_STAGE_VERTEX_BIT|VK_SHADER_STAGE_FRAGMENT_BIT;
    VkPushConstantRange pr{stages,0,128};VkPipelineLayoutCreateInfo pl{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};pl.setLayoutCount=pl.pushConstantRangeCount=1;pl.pSetLayouts=&set_layout;pl.pPushConstantRanges=&pr;
    VkPipelineLayout layout{};check(vkCreatePipelineLayout(c.device,&pl,nullptr,&layout));
    VkPipelineShaderStageCreateInfo shaders[2]{};
    shaders[0]={VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,nullptr,0,VK_SHADER_STAGE_VERTEX_BIT,load_module(c,j.value("vertex_shader",path("vs.spv"))),"main",nullptr};
    shaders[1]={VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,nullptr,0,VK_SHADER_STAGE_FRAGMENT_BIT,load_module(c,j.value("fragment_shader",path("fs.spv"))),"main",nullptr};
    VkPipelineVertexInputStateCreateInfo vertex{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
    VkPipelineInputAssemblyStateCreateInfo assembly{VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};assembly.topology=VK_PRIMITIVE_TOPOLOGY_TRIANGLE_STRIP;
    const auto vp=j.at("viewport");float xs=vp.at("xscale"),ys=vp.at("yscale"),xo=vp.at("xoffset"),yo=vp.at("yoffset");VkViewport viewport{xo-xs,yo-ys,2*xs,2*ys,0,1};VkRect2D scissor{{0,0},{width,height}};
    VkPipelineViewportStateCreateInfo view{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};view.viewportCount=view.scissorCount=1;view.pViewports=&viewport;view.pScissors=&scissor;
    VkPipelineRasterizationStateCreateInfo raster{VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};raster.lineWidth=1;
    VkPipelineMultisampleStateCreateInfo ms{VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};ms.rasterizationSamples=VK_SAMPLE_COUNT_1_BIT;
    VkPipelineColorBlendAttachmentState blend_states[2]{};
    for(unsigned i=0;i<2;++i){auto& b=blend_states[i];b.colorWriteMask=15;b.blendEnable=VK_TRUE;b.srcColorBlendFactor=i?VK_BLEND_FACTOR_SRC_ALPHA:VK_BLEND_FACTOR_ONE;b.dstColorBlendFactor=VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;b.srcAlphaBlendFactor=b.srcColorBlendFactor;b.dstAlphaBlendFactor=b.dstColorBlendFactor;}
    VkPipelineColorBlendStateCreateInfo blend{VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};blend.attachmentCount=2;blend.pAttachments=blend_states;
    VkFormat formats[]={VK_FORMAT_R16G16B16A16_SFLOAT,VK_FORMAT_R8_UNORM};
    VkPipelineRenderingCreateInfo rendering{VK_STRUCTURE_TYPE_PIPELINE_RENDERING_CREATE_INFO};rendering.colorAttachmentCount=2;rendering.pColorAttachmentFormats=formats;
    VkGraphicsPipelineCreateInfo pi{VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO};pi.pNext=&rendering;pi.stageCount=2;pi.pStages=shaders;pi.pVertexInputState=&vertex;pi.pInputAssemblyState=&assembly;pi.pViewportState=&view;pi.pRasterizationState=&raster;pi.pMultisampleState=&ms;pi.pColorBlendState=&blend;pi.layout=layout;
    VkPipeline pipeline{};check(vkCreateGraphicsPipelines(c.device,VK_NULL_HANDLE,1,&pi,nullptr,&pipeline));
    require(sync_errors+other_errors==0,"Native UI pipeline validation failed");
    std::unique_ptr<NativeBloom> native_bloom;if(j.contains("native_bloom")){require(has_post,"Native bloom requires DoPost");native_bloom=std::make_unique<NativeBloom>(c,j.at("native_bloom"),target);}
    std::unique_ptr<NativePost> post;if(has_post)post=std::make_unique<NativePost>(c,j.at("postprocess"),target.view);
    VkQueryPoolCreateInfo qp{VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO};qp.queryType=VK_QUERY_TYPE_TIMESTAMP;qp.queryCount=2;VkQueryPool queries{};if(profile)check(vkCreateQueryPool(c.device,&qp,nullptr,&queries));VkPhysicalDeviceProperties properties{};vkGetPhysicalDeviceProperties(c.physical,&properties);
    uint64_t frames=0;unsigned draw_count=1;
    do {
    if(stream){unsigned n=0;if(!std::cin.read(reinterpret_cast<char*>(&n),4))break;if(n==0){std::cerr<<"stream_stop_received"<<std::endl;break;}require(n>=1&&n<=8,"Native UI stream count");draw_count=n;for(unsigned i=0;i<n;++i){require(bool(std::cin.read(static_cast<char*>(geometry.data)+i*524,524)),"Truncated native UI stream record");}}
    auto cpu_start=std::chrono::steady_clock::now();c.begin(0);auto cmd=c.commands[0];if(profile){vkCmdResetQueryPool(cmd,queries,0,2);vkCmdWriteTimestamp(cmd,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,queries,0);}target.barrier(cmd,VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,1,1);bloom.barrier(cmd,VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,1,1);
    VkRenderingAttachmentInfo attachments[2]{};for(unsigned i=0;i<2;++i){auto& a=attachments[i];a.sType=VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_INFO;a.imageView=i?bloom.view:target.view;a.imageLayout=VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;a.loadOp=VK_ATTACHMENT_LOAD_OP_CLEAR;a.storeOp=VK_ATTACHMENT_STORE_OP_STORE;}
    VkRenderingInfo ri{VK_STRUCTURE_TYPE_RENDERING_INFO};ri.renderArea=scissor;ri.layerCount=1;ri.colorAttachmentCount=2;ri.pColorAttachments=attachments;
    vkCmdBeginRendering(cmd,&ri);vkCmdBindPipeline(cmd,VK_PIPELINE_BIND_POINT_GRAPHICS,pipeline);vkCmdBindDescriptorSets(cmd,VK_PIPELINE_BIND_POINT_GRAPHICS,layout,0,1,&set,0,nullptr);
    auto push=read(path("push-data.bin"));require(push.size()==128,"Native UI push constant size");if(stream){for(unsigned i=0;i<draw_count;++i){if(i){vkCmdEndRendering(cmd);VkMemoryBarrier barrier{VK_STRUCTURE_TYPE_MEMORY_BARRIER};barrier.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;barrier.dstAccessMask=VK_ACCESS_SHADER_WRITE_BIT|VK_ACCESS_SHADER_READ_BIT;vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_VERTEX_SHADER_BIT|VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,VK_PIPELINE_STAGE_VERTEX_SHADER_BIT|VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,0,1,&barrier,0,nullptr,0,nullptr);for(auto& attachment:attachments)attachment.loadOp=VK_ATTACHMENT_LOAD_OP_LOAD;vkCmdBeginRendering(cmd,&ri);}std::memcpy(push.data()+24,&i,4);std::memcpy(push.data()+44,&i,4);vkCmdPushConstants(cmd,layout,stages,0,128,push.data());vkCmdDraw(cmd,4,1,0,0);}}
    else{vkCmdPushConstants(cmd,layout,stages,0,128,push.data());vkCmdDraw(cmd,4,1,0,0);}vkCmdEndRendering(cmd);
    if(has_post){if(native_bloom)native_bloom->draw(cmd);else target.barrier(cmd,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,1,1);post->draw(cmd);}else target.barrier(cmd,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,1,1);bloom.barrier(cmd,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,1,1);
    VkBufferImageCopy copy{};copy.imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0,0,1};copy.imageExtent={width,height,1};if(stream&&!full_overlay){VkBufferImageCopy crops[3]{};const unsigned centers[]={842,960,1078};for(unsigned i=0;i<3;++i){crops[i].bufferOffset=size_t(i)*165*165*8;crops[i].imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0,0,1};crops[i].imageOffset={int(centers[i])-82,30,0};crops[i].imageExtent={165,165,1};}vkCmdCopyImageToBuffer(cmd,target.image,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,result.handle,3,crops);}
    else{vkCmdCopyImageToBuffer(cmd,has_post?post->output.image:target.image,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,result.handle,1,&copy);if(!stream)vkCmdCopyImageToBuffer(cmd,bloom.image,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,bloom_result.handle,1,&copy);}
    VkMemoryBarrier host{VK_STRUCTURE_TYPE_MEMORY_BARRIER};host.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;host.dstAccessMask=VK_ACCESS_HOST_READ_BIT;vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_HOST_BIT,0,1,&host,0,nullptr,0,nullptr);
    if(profile)vkCmdWriteTimestamp(cmd,VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,queries,1);check(vkEndCommandBuffer(cmd));c.submit(0,1,true);auto cpu_render=std::chrono::steady_clock::now();
    const auto* f=static_cast<const uint8_t*>(faults.data);require(std::all_of(f,f+faults.bytes,[](auto x){return x==0;}),"Native UI requested an uncaptured dynamic buffer");
    if(stream){if(output_shared){if(has_post)ui_videoout_rgba(static_cast<const uint32_t*>(result.data),static_cast<uint8_t*>(output_shared),output_pixels);else if(display_rgba)ui_display_rgba(static_cast<const uint16_t*>(result.data),static_cast<uint8_t*>(output_shared),output_pixels);else std::memcpy(output_shared,result.data,output_pixels*8);ui_binary->write("UIOK",4);}else ui_binary->write(static_cast<char*>(result.data),output_pixels*(has_post?4:8));ui_binary->flush();++frames;if(profile&&frames%10==0){uint64_t stamps[2]{};check(vkGetQueryPoolResults(c.device,queries,0,2,sizeof(stamps),stamps,8,VK_QUERY_RESULT_64_BIT|VK_QUERY_RESULT_WAIT_BIT));auto cpu_end=std::chrono::steady_clock::now();std::cerr<<"stream_frame="<<frames<<" gpu_ms="<<(stamps[1]-stamps[0])*properties.limits.timestampPeriod/1e6<<" render_cpu_ms="<<std::chrono::duration<double,std::milli>(cpu_render-cpu_start).count()<<" output_ms="<<std::chrono::duration<double,std::milli>(cpu_end-cpu_render).count()<<std::endl;}continue;}
    std::ofstream out(j.at("output").get<std::string>(),std::ios::binary);out.write(static_cast<char*>(result.data),width*height*(has_post?4:8));
    std::ofstream glow(j.at("bloom_output").get<std::string>(),std::ios::binary);glow.write(static_cast<char*>(bloom_result.data),width*height);
    }while(stream);
    std::cerr<<"stream_cleanup"<<std::endl;
    if(output_shared)UnmapViewOfFile(output_shared);if(output_mapping)CloseHandle(output_mapping);
    vkDestroyQueryPool(c.device,queries,nullptr);vkDestroyPipeline(c.device,pipeline,nullptr);for(auto& s:shaders)vkDestroyShaderModule(c.device,s.module,nullptr);vkDestroyPipelineLayout(c.device,layout,nullptr);vkDestroyDescriptorPool(c.device,pool,nullptr);vkDestroyDescriptorSetLayout(c.device,set_layout,nullptr);for(auto s:samplers)vkDestroySampler(c.device,s,nullptr);
}
int main(int argc,char** argv){try{require(argc==2,"Native UI replay configuration required");json j;std::ifstream(argv[1])>>j;if(j.value("stream",false)){_setmode(_fileno(stdin),_O_BINARY);_setmode(_fileno(stdout),_O_BINARY);}auto* saved=std::cout.rdbuf();std::ostream output(saved);ui_binary=&output;std::cout.rdbuf(std::cerr.rdbuf());ui_portable_device=j.contains("fragment_shader");Context c(j.value("validation",true));replay_ui(c,j);std::cout.rdbuf(saved);std::cerr<<"native_ui_validation_errors="<<sync_errors+other_errors<<std::endl;return sync_errors+other_errors?2:0;}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}
