#include "context.h"
#include <nlohmann/json.hpp>
#include <memory>
#include <map>
using nlohmann::json;
static std::vector<uint8_t> read(const std::string&path){
    std::ifstream f(path,std::ios::binary|std::ios::ate);require(bool(f),("missing "+path).c_str());
    std::vector<uint8_t>b(size_t(f.tellg()));f.seekg(0);f.read((char*)b.data(),b.size());return b;
}
struct Buffer{
    Context&c;VkBuffer handle{};VkDeviceMemory memory{};void*data{};size_t bytes;uint64_t address{};
    Buffer(Context&ctx,size_t n):c(ctx),bytes(std::max<size_t>(n,256)){
        VkBufferCreateInfo bi{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};bi.size=bytes;
        bi.usage=VK_BUFFER_USAGE_STORAGE_BUFFER_BIT|VK_BUFFER_USAGE_TRANSFER_SRC_BIT|VK_BUFFER_USAGE_TRANSFER_DST_BIT|VK_BUFFER_USAGE_INDEX_BUFFER_BIT|VK_BUFFER_USAGE_SHADER_DEVICE_ADDRESS_BIT;
        check(vkCreateBuffer(c.device,&bi,nullptr,&handle));VkMemoryRequirements mr{};vkGetBufferMemoryRequirements(c.device,handle,&mr);
        VkMemoryAllocateFlagsInfo flags{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_FLAGS_INFO};flags.flags=VK_MEMORY_ALLOCATE_DEVICE_ADDRESS_BIT;
        VkMemoryAllocateInfo ai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};ai.pNext=&flags;ai.allocationSize=mr.size;
        ai.memoryTypeIndex=c.memory_type(mr.memoryTypeBits,VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        check(vkAllocateMemory(c.device,&ai,nullptr,&memory));check(vkBindBufferMemory(c.device,handle,memory,0));
        check(vkMapMemory(c.device,memory,0,bytes,0,&data));memset(data,0,bytes);
        VkBufferDeviceAddressInfo a{VK_STRUCTURE_TYPE_BUFFER_DEVICE_ADDRESS_INFO};a.buffer=handle;address=vkGetBufferDeviceAddress(c.device,&a);
    }
    Buffer(Context&c,const std::vector<uint8_t>&v):Buffer(c,v.size()){memcpy(data,v.data(),v.size());}
    ~Buffer(){vkUnmapMemory(c.device,memory);vkDestroyBuffer(c.device,handle,nullptr);vkFreeMemory(c.device,memory,nullptr);}
};
struct Image{
    Context&c;VkImage handle{};VkDeviceMemory memory{};VkImageView view{};VkFormat format;
    uint32_t width,height,levels;VkImageAspectFlags aspect;VkImageLayout layout=VK_IMAGE_LAYOUT_UNDEFINED;
    Image(Context&ctx,uint32_t w,uint32_t h,VkFormat f,uint32_t lv,bool target,const json& mapping):c(ctx),format(f),width(w),height(h),levels(lv){
        aspect=f==VK_FORMAT_D32_SFLOAT?VK_IMAGE_ASPECT_DEPTH_BIT:VK_IMAGE_ASPECT_COLOR_BIT;
        VkImageCreateInfo im{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO};im.imageType=VK_IMAGE_TYPE_2D;im.format=f;im.extent={w,h,1};im.mipLevels=lv;im.arrayLayers=1;im.samples=VK_SAMPLE_COUNT_1_BIT;im.tiling=VK_IMAGE_TILING_OPTIMAL;
        im.usage=VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_TRANSFER_SRC_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT|(target?VK_IMAGE_USAGE_STORAGE_BIT:0);
        check(vkCreateImage(c.device,&im,nullptr,&handle));VkMemoryRequirements mr{};vkGetImageMemoryRequirements(c.device,handle,&mr);
        VkMemoryAllocateInfo ai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};ai.allocationSize=mr.size;ai.memoryTypeIndex=c.memory_type(mr.memoryTypeBits,VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        check(vkAllocateMemory(c.device,&ai,nullptr,&memory));check(vkBindImageMemory(c.device,handle,memory,0));
        VkImageViewCreateInfo vi{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};vi.image=handle;vi.viewType=VK_IMAGE_VIEW_TYPE_2D;vi.format=f;vi.subresourceRange={aspect,0,lv,0,1};vi.components={VkComponentSwizzle(int(mapping[0])),VkComponentSwizzle(int(mapping[1])),VkComponentSwizzle(int(mapping[2])),VkComponentSwizzle(int(mapping[3]))};
        check(vkCreateImageView(c.device,&vi,nullptr,&view));
    }
    void transition(VkCommandBuffer cmd,VkImageLayout to){
        VkImageMemoryBarrier b{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};b.image=handle;b.subresourceRange={aspect,0,levels,0,1};
        b.srcQueueFamilyIndex=b.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;b.oldLayout=layout;b.newLayout=to;
        b.srcAccessMask=layout==VK_IMAGE_LAYOUT_UNDEFINED?0:VK_ACCESS_MEMORY_WRITE_BIT|VK_ACCESS_MEMORY_READ_BIT;b.dstAccessMask=VK_ACCESS_MEMORY_READ_BIT|VK_ACCESS_MEMORY_WRITE_BIT;
        vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,0,0,nullptr,0,nullptr,1,&b);layout=to;
    }
    void upload(const std::vector<std::string>&files){
        require(files.size()==1,"captured base mip only");std::vector<uint8_t> all;std::vector<VkBufferImageCopy> copies;
        for(uint32_t m=0;m<files.size();m++){auto b=read(files[m]);VkBufferImageCopy r{};r.bufferOffset=all.size();r.imageSubresource={aspect,m,0,1};r.imageExtent={std::max(1u,width>>m),std::max(1u,height>>m),1};copies.push_back(r);all.insert(all.end(),b.begin(),b.end());}
        Buffer staging(c,all);c.begin(0);auto cmd=c.commands[0];transition(cmd,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);
        vkCmdCopyBufferToImage(cmd,staging.handle,handle,layout,copies.size(),copies.data());transition(cmd,VK_IMAGE_LAYOUT_GENERAL);
        check(vkEndCommandBuffer(cmd));c.submit(0,1,true);
    }
    void save(const std::string&path,size_t bytes){
        Buffer dst(c,bytes);c.begin(0);auto cmd=c.commands[0];transition(cmd,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);
        VkBufferImageCopy copy{};copy.imageSubresource={aspect,0,0,1};copy.imageExtent={width,height,1};vkCmdCopyImageToBuffer(cmd,handle,layout,dst.handle,1,&copy);
        VkMemoryBarrier host{VK_STRUCTURE_TYPE_MEMORY_BARRIER};host.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;host.dstAccessMask=VK_ACCESS_HOST_READ_BIT;
        vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_HOST_BIT,0,1,&host,0,nullptr,0,nullptr);
        check(vkEndCommandBuffer(cmd));c.submit(0,1,true);std::ofstream out(path,std::ios::binary);out.write((char*)dst.data,bytes);
    }
    ~Image(){vkDestroyImageView(c.device,view,nullptr);vkDestroyImage(c.device,handle,nullptr);vkFreeMemory(c.device,memory,nullptr);}
};
static VkSampler sampler(Context&c,const json&j){
    VkSamplerCreateInfo s{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};s.magFilter=VkFilter(int(j["mag"]));s.minFilter=VkFilter(int(j["min"]));s.mipmapMode=int(j["mip"])==2?VK_SAMPLER_MIPMAP_MODE_LINEAR:VK_SAMPLER_MIPMAP_MODE_NEAREST;
    auto clamp=[](int i){require(i==0||i==2,"unsupported sampler clamp");return i==0?VK_SAMPLER_ADDRESS_MODE_REPEAT:VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;};
    s.addressModeU=clamp(j["clamp_x"]);s.addressModeV=clamp(j["clamp_y"]);s.addressModeW=clamp(j["clamp_z"]);s.minLod=j["min_lod"];s.maxLod=j["max_lod"];s.mipLodBias=j["bias"];s.maxAnisotropy=1;
    require(j["border"]==0,"border");s.borderColor=VK_BORDER_COLOR_FLOAT_TRANSPARENT_BLACK;VkSampler result;check(vkCreateSampler(c.device,&s,nullptr,&result));return result;
}

static void run(Context&c,const json&j){
    label=std::string(j["capture"])+"-"+std::to_string(int(j["event"]));
    std::vector<std::unique_ptr<Image>> images;
    std::vector<VkDescriptorSetLayoutBinding> bindings;
    std::vector<VkDescriptorBufferInfo> bis;std::vector<VkDescriptorImageInfo> iis;std::vector<VkWriteDescriptorSet> writes;
    bis.reserve(16);iis.reserve(16);writes.reserve(16);
    Buffer flat(c,read(j["flat"]));
    auto add=[&](uint32_t binding,VkDescriptorType type){bindings.push_back({binding,type,1,VK_SHADER_STAGE_COMPUTE_BIT,nullptr});VkWriteDescriptorSet w{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};w.dstBinding=binding;w.descriptorCount=1;w.descriptorType=type;writes.push_back(w);};
    add(j["flat_binding"],VK_DESCRIPTOR_TYPE_STORAGE_BUFFER);bis.push_back({flat.handle,0,read(j["flat"]).size()});writes.back().pBufferInfo=&bis.back();
    for(const auto& im:j["images"]){
        if(im["null"]){images.push_back(nullptr);iis.push_back({VK_NULL_HANDLE,VK_NULL_HANDLE,VK_IMAGE_LAYOUT_GENERAL});}
        else{
            images.push_back(std::make_unique<Image>(c,int(im["width"]),int(im["height"]),VkFormat(int(im["view_format"])),int(im["levels"]),bool(im["written"]),im["mapping"]));
            images.back()->upload({im["pre"]});
            iis.push_back({VK_NULL_HANDLE,images.back()->view,VK_IMAGE_LAYOUT_GENERAL});
        }
        add(im["binding"],bool(im["written"])?VK_DESCRIPTOR_TYPE_STORAGE_IMAGE:VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE);writes.back().pImageInfo=&iis.back();
    }
    auto smplr=sampler(c,j["sampler"]);iis.push_back({smplr,VK_NULL_HANDLE,VK_IMAGE_LAYOUT_UNDEFINED});add(j["sampler_binding"],VK_DESCRIPTOR_TYPE_SAMPLER);writes.back().pImageInfo=&iis.back();
    VkDescriptorSetLayoutCreateInfo li{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};li.bindingCount=bindings.size();li.pBindings=bindings.data();VkDescriptorSetLayout layout;check(vkCreateDescriptorSetLayout(c.device,&li,nullptr,&layout));
    std::array<VkDescriptorPoolSize,4> pools{{{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1},{VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,2},{VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE,8},{VK_DESCRIPTOR_TYPE_SAMPLER,1}}};
    VkDescriptorPoolCreateInfo dpi{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};dpi.maxSets=1;dpi.poolSizeCount=pools.size();dpi.pPoolSizes=pools.data();VkDescriptorPool pool;check(vkCreateDescriptorPool(c.device,&dpi,nullptr,&pool));
    VkDescriptorSetAllocateInfo da{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};da.descriptorPool=pool;da.descriptorSetCount=1;da.pSetLayouts=&layout;VkDescriptorSet set;check(vkAllocateDescriptorSets(c.device,&da,&set));
    for(auto&w:writes)w.dstSet=set;vkUpdateDescriptorSets(c.device,writes.size(),writes.data(),0,nullptr);
    VkPushConstantRange pushrange{VK_SHADER_STAGE_COMPUTE_BIT,0,128};VkPipelineLayoutCreateInfo pli{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};pli.setLayoutCount=1;pli.pSetLayouts=&layout;pli.pushConstantRangeCount=1;pli.pPushConstantRanges=&pushrange;VkPipelineLayout pl;check(vkCreatePipelineLayout(c.device,&pli,nullptr,&pl));
    auto module=load_module(c,j["spirv"]);VkPipelineShaderStageRequiredSubgroupSizeCreateInfo sg{VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_REQUIRED_SUBGROUP_SIZE_CREATE_INFO};sg.requiredSubgroupSize=64;
    require(j["context"][4]==64,"exact subgroup required");VkComputePipelineCreateInfo pi{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};pi.flags=VK_PIPELINE_CREATE_DISPATCH_BASE_BIT;pi.stage={VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO};pi.stage.pNext=&sg;pi.stage.stage=VK_SHADER_STAGE_COMPUTE_BIT;pi.stage.module=module;pi.stage.pName="main";pi.layout=pl;VkPipeline pipeline;check(vkCreateComputePipelines(c.device,VK_NULL_HANDLE,1,&pi,nullptr,&pipeline));
    auto push=read(j["push"]);require(push.size()==128,"push bytes");c.begin(0);auto cmd=c.commands[0];vkCmdBindPipeline(cmd,VK_PIPELINE_BIND_POINT_COMPUTE,pipeline);vkCmdBindDescriptorSets(cmd,VK_PIPELINE_BIND_POINT_COMPUTE,pl,0,1,&set,0,nullptr);vkCmdPushConstants(cmd,pl,VK_SHADER_STAGE_COMPUTE_BIT,0,128,push.data());
    const auto& d=j["dispatch"];vkCmdDispatchBase(cmd,d[0],d[1],d[2],d[3],d[4],d[5]);check(vkEndCommandBuffer(cmd));c.submit(0,1,true);
    for(unsigned i=0;i<images.size();i++)if(bool(j["images"][i]["written"])){
        std::string path=std::string(j["out"])+"-"+std::string(j["images"][i]["role"])+".bin";images[i]->save(path,j["images"][i]["bytes"]);
        auto a=read(path),b=read(j["images"][i]["post"]);require(a.size()==b.size(),"output size");size_t mismatches=0;for(size_t k=0;k<a.size();k++)mismatches+=a[k]!=b[k];
        std::cout<<"result "<<label<<" "<<j["images"][i]["role"]<<" bytes="<<a.size()<<" mismatching_bytes="<<mismatches<<std::endl;
    }
    vkDestroyPipeline(c.device,pipeline,nullptr);vkDestroyShaderModule(c.device,module,nullptr);vkDestroyPipelineLayout(c.device,pl,nullptr);vkDestroyDescriptorPool(c.device,pool,nullptr);vkDestroyDescriptorSetLayout(c.device,layout,nullptr);vkDestroySampler(c.device,smplr,nullptr);
}
int main(int argc,char**argv){try{require(argc==2,"cases file");std::ifstream f(argv[1]);json cases;f>>cases;Context c;for(const auto&j:cases)run(c,j);std::cout<<"validation_errors="<<sync_errors+other_errors<<std::endl;return sync_errors+other_errors?2:0;}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
