// Captured Dreams BloomPyramid shaders and uniform records. No blur replacement.
struct NativeBloomPass {
 Context& c; Buffer flat; VkDescriptorSetLayout set_layout{};VkDescriptorPool pool{};VkDescriptorSet set{};
 VkPipelineLayout layout{};VkPipeline pipeline{};VkShaderModule shader{};VkSampler sampler{};
 unsigned width,height;DrawImage& source;DrawImage& destination;
 NativeBloomPass(Context& ctx,const json& j,bool up,DrawImage& src,DrawImage& dst,unsigned w,unsigned h,bool first):
  c(ctx),flat(c,read(j.at(up?"up_flat":first?"down_flat":"down_rest_flat"))),width(w),height(h),source(src),destination(dst){
  auto* words=static_cast<uint32_t*>(flat.data);words[16]=w;words[17]=h;
  // The descriptors contain native image metadata, but the SPIR-V image bindings
  // resolve to these standalone views. The captured scalar parameters are retained.
  auto s=j.at("sampler");VkSamplerCreateInfo si{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};si.magFilter=VkFilter(int(s.at("mag")));si.minFilter=VkFilter(int(s.at("min")));si.mipmapMode=VK_SAMPLER_MIPMAP_MODE_LINEAR;
  auto clamp=[](int v){require(v==6,"Unexpected native bloom border mode");return VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_BORDER;};si.addressModeU=clamp(s.at("clamp_x"));si.addressModeV=clamp(s.at("clamp_y"));si.addressModeW=clamp(s.at("clamp_z"));si.minLod=s.at("min_lod");si.maxLod=s.at("max_lod");si.mipLodBias=s.at("bias");check(vkCreateSampler(c.device,&si,nullptr,&sampler));
  unsigned sampled=up?2:1,storage=up?1:2;
  VkDescriptorSetLayoutBinding bindings[]={{0,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},{1,up?VK_DESCRIPTOR_TYPE_STORAGE_IMAGE:VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE,1,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},{2,up?VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE:VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,1,VK_SHADER_STAGE_COMPUTE_BIT,nullptr},{3,VK_DESCRIPTOR_TYPE_SAMPLER,1,VK_SHADER_STAGE_COMPUTE_BIT,nullptr}};
  VkDescriptorSetLayoutCreateInfo sl{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};sl.bindingCount=4;sl.pBindings=bindings;check(vkCreateDescriptorSetLayout(c.device,&sl,nullptr,&set_layout));
  VkDescriptorPoolSize sizes[]={{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1},{VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,1},{VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE,1},{VK_DESCRIPTOR_TYPE_SAMPLER,1}};VkDescriptorPoolCreateInfo dp{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};dp.maxSets=1;dp.poolSizeCount=4;dp.pPoolSizes=sizes;check(vkCreateDescriptorPool(c.device,&dp,nullptr,&pool));VkDescriptorSetAllocateInfo da{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};da.descriptorPool=pool;da.descriptorSetCount=1;da.pSetLayouts=&set_layout;check(vkAllocateDescriptorSets(c.device,&da,&set));
  VkDescriptorBufferInfo bi{flat.handle,0,VK_WHOLE_SIZE};VkDescriptorImageInfo ii[4]{};ii[sampled]={VK_NULL_HANDLE,source.view,VK_IMAGE_LAYOUT_GENERAL};ii[storage]={VK_NULL_HANDLE,destination.view,VK_IMAGE_LAYOUT_GENERAL};ii[3]={sampler,VK_NULL_HANDLE,VK_IMAGE_LAYOUT_UNDEFINED};VkWriteDescriptorSet writes[4]{};
  for(unsigned i=0;i<4;++i){auto& wri=writes[i];wri.sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;wri.dstSet=set;wri.dstBinding=i;wri.descriptorCount=1;wri.descriptorType=bindings[i].descriptorType;if(i==0)wri.pBufferInfo=&bi;else wri.pImageInfo=&ii[i];}vkUpdateDescriptorSets(c.device,4,writes,0,nullptr);
  VkPushConstantRange pr{VK_SHADER_STAGE_COMPUTE_BIT,0,128};VkPipelineLayoutCreateInfo pl{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};pl.setLayoutCount=1;pl.pSetLayouts=&set_layout;pl.pushConstantRangeCount=1;pl.pPushConstantRanges=&pr;check(vkCreatePipelineLayout(c.device,&pl,nullptr,&layout));
  shader=load_module(c,j.at(up?"up_shader":"down_shader"));VkComputePipelineCreateInfo pi{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};pi.layout=layout;pi.stage={VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,nullptr,0,VK_SHADER_STAGE_COMPUTE_BIT,shader,"main",nullptr};check(vkCreateComputePipelines(c.device,VK_NULL_HANDLE,1,&pi,nullptr,&pipeline));
 }
 void dispatch(VkCommandBuffer cmd){vkCmdBindPipeline(cmd,VK_PIPELINE_BIND_POINT_COMPUTE,pipeline);vkCmdBindDescriptorSets(cmd,VK_PIPELINE_BIND_POINT_COMPUTE,layout,0,1,&set,0,nullptr);uint32_t push[32]{};vkCmdPushConstants(cmd,layout,VK_SHADER_STAGE_COMPUTE_BIT,0,128,push);vkCmdDispatch(cmd,(width+7)/8,(height+7)/8,1);destination.barrier(cmd,VK_IMAGE_LAYOUT_GENERAL,VK_IMAGE_LAYOUT_GENERAL,1,1);}
 ~NativeBloomPass(){vkDestroyPipeline(c.device,pipeline,nullptr);vkDestroyShaderModule(c.device,shader,nullptr);vkDestroyPipelineLayout(c.device,layout,nullptr);vkDestroyDescriptorPool(c.device,pool,nullptr);vkDestroyDescriptorSetLayout(c.device,set_layout,nullptr);vkDestroySampler(c.device,sampler,nullptr);}
};
struct NativeBloom {
 Context& c;DrawImage& original;std::vector<std::unique_ptr<DrawImage>> levels;std::vector<std::unique_ptr<NativeBloomPass>> down,up;
 NativeBloom(Context& ctx,const json& j,DrawImage& image):c(ctx),original(image){
  unsigned w=1920,h=1080;DrawImage* prior=&image;std::vector<std::pair<unsigned,unsigned>> dimensions{{w,h}};
  for(unsigned i=0;i<8;++i){w=(w+1)/2;h=(h+1)/2;dimensions.emplace_back(w,h);levels.push_back(std::make_unique<DrawImage>(c,w,h,1,1,VK_FORMAT_R16G16B16A16_SFLOAT,VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_SAMPLED_BIT));down.push_back(std::make_unique<NativeBloomPass>(c,j,false,*prior,*levels.back(),w,h,i==0));prior=levels.back().get();}
  for(unsigned i=8;i>0;--i){auto& destination=i==1?original:*levels[i-2];auto [x,y]=dimensions[i-1];up.push_back(std::make_unique<NativeBloomPass>(c,j,true,*levels[i-1],destination,x,y,false));}
 }
 void draw(VkCommandBuffer cmd){original.barrier(cmd,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_GENERAL,1,1);for(auto& l:levels)l->barrier(cmd,VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_GENERAL,1,1);for(auto& p:down)p->dispatch(cmd);for(auto& p:up)p->dispatch(cmd);original.barrier(cmd,VK_IMAGE_LAYOUT_GENERAL,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,1,1);}
};
