#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#define VULKAN_HPP_NO_STRUCT_CONSTRUCTORS
#define VULKAN_HPP_NO_UNION_CONSTRUCTORS
#include <windows.h>
#include <vulkan/vulkan.hpp>
#include <array>
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
static unsigned sync_errors{}, other_errors{};
static std::string label;
static void check(VkResult r) {
    if (r != VK_SUCCESS) throw std::runtime_error("Vulkan error " + std::to_string(r));
}
static void require(bool b, const char* text) { if (!b) throw std::runtime_error(text); }
static VKAPI_ATTR VkBool32 VKAPI_CALL message(VkDebugUtilsMessageSeverityFlagBitsEXT,
    VkDebugUtilsMessageTypeFlagsEXT, const VkDebugUtilsMessengerCallbackDataEXT* d, void*) {
    if (d->pMessageIdName && strstr(d->pMessageIdName,"SYNC-HAZARD")) ++sync_errors;
    else ++other_errors;
    std::cout << "validation " << label << " " << d->pMessageIdName << " " << d->pMessage << '\n';
    return VK_FALSE;
}

struct Context {
    VkInstance instance{};
    VkPhysicalDevice physical{};
    VkDevice device{};
    VkQueue queue{};
    VkShaderStageFlags explicit_subgroup_stages{};
    VkCommandPool pool{};
    VkCommandBuffer commands[2]{};
    VkPhysicalDeviceMemoryProperties memory{};
    VkDebugUtilsMessengerEXT messenger{};
    PFN_vkDestroyDebugUtilsMessengerEXT destroy_debug{};
    explicit Context(bool validation = true) {
        VkBool32 yes=VK_TRUE,no=VK_FALSE;
        const char* layer="VK_LAYER_KHRONOS_validation";
        VkLayerSettingEXT opts[]={
            {layer,"validate_core",VK_LAYER_SETTING_TYPE_BOOL32_EXT,1,&yes},
            {layer,"validate_sync",VK_LAYER_SETTING_TYPE_BOOL32_EXT,1,&yes},
            {layer,"syncval_shader_accesses_heuristic",VK_LAYER_SETTING_TYPE_BOOL32_EXT,1,&yes},
            {layer,"enable_message_limit",VK_LAYER_SETTING_TYPE_BOOL32_EXT,1,&no},
            {layer,"syncval_submit_time_validation",VK_LAYER_SETTING_TYPE_BOOL32_EXT,1,&yes},
            {layer,"gpuav_enable",VK_LAYER_SETTING_TYPE_BOOL32_EXT,1,&no}};
        VkLayerSettingsCreateInfoEXT settings{VK_STRUCTURE_TYPE_LAYER_SETTINGS_CREATE_INFO_EXT};
        settings.settingCount=6; settings.pSettings=opts;
        VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO}; app.apiVersion=VK_API_VERSION_1_3;
        const char* extensions[]={VK_EXT_DEBUG_UTILS_EXTENSION_NAME,VK_EXT_LAYER_SETTINGS_EXTENSION_NAME};
        VkInstanceCreateInfo ii{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO}; ii.pNext=&settings;
        ii.pApplicationInfo=&app;
        if (validation) {
            ii.enabledLayerCount=1; ii.ppEnabledLayerNames=&layer;
            ii.enabledExtensionCount=2; ii.ppEnabledExtensionNames=extensions;
        } else {
            ii.pNext=nullptr;
        }
        check(vkCreateInstance(&ii,nullptr,&instance));
        if (validation) {
            char loaded_path[32768]{};
            auto loaded=GetModuleHandleA("VkLayer_khronos_validation.dll");
            require(loaded && GetModuleFileNameA(loaded,loaded_path,sizeof(loaded_path)),"validation DLL unavailable");
            std::cout << "loaded_layer=" << loaded_path << '\n';
            VkDebugUtilsMessengerCreateInfoEXT mi{VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT};
            mi.messageSeverity=VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT;
            mi.messageType=VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT; mi.pfnUserCallback=message;
            auto create=(PFN_vkCreateDebugUtilsMessengerEXT)vkGetInstanceProcAddr(instance,"vkCreateDebugUtilsMessengerEXT");
            destroy_debug=(PFN_vkDestroyDebugUtilsMessengerEXT)vkGetInstanceProcAddr(instance,"vkDestroyDebugUtilsMessengerEXT");
            check(create(instance,&mi,nullptr,&messenger));
        }
        uint32_t n{}; check(vkEnumeratePhysicalDevices(instance,&n,nullptr));
        std::vector<VkPhysicalDevice> devices(n); check(vkEnumeratePhysicalDevices(instance,&n,devices.data()));
        const char* device_ext[] = {
            "VK_KHR_fragment_shader_barycentric",
            "VK_EXT_robustness2",
            "VK_EXT_depth_clip_enable",
            "VK_KHR_workgroup_memory_explicit_layout",
        };
        uint32_t family = 0;
        bool discrete = false;
        for (auto candidate : devices) {
            VkPhysicalDeviceProperties props{};
            vkGetPhysicalDeviceProperties(candidate, &props);
            if (props.apiVersion < VK_API_VERSION_1_3) continue;
            VkPhysicalDeviceSubgroupSizeControlProperties subgroup{
                VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SUBGROUP_SIZE_CONTROL_PROPERTIES};
            VkPhysicalDeviceSubgroupProperties default_subgroup{
                VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SUBGROUP_PROPERTIES, &subgroup};
            VkPhysicalDeviceProperties2 properties{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2,
                                                    &default_subgroup};
            vkGetPhysicalDeviceProperties2(candidate, &properties);
            constexpr VkShaderStageFlags stages = VK_SHADER_STAGE_FRAGMENT_BIT |
                                                   VK_SHADER_STAGE_COMPUTE_BIT;
            if ((default_subgroup.supportedStages & stages) != stages ||
                !(default_subgroup.supportedOperations & VK_SUBGROUP_FEATURE_BALLOT_BIT)) continue;
            const VkShaderStageFlags explicit_size = default_subgroup.subgroupSize == 32 ?
                0 : (subgroup.requiredSubgroupSizeStages & stages);
            if (default_subgroup.subgroupSize != 32 &&
                (subgroup.minSubgroupSize > 32 || subgroup.maxSubgroupSize < 32 ||
                 explicit_size != stages)) continue;
            uint32_t extension_count = 0;
            check(vkEnumerateDeviceExtensionProperties(candidate, nullptr, &extension_count, nullptr));
            std::vector<VkExtensionProperties> extensions(extension_count);
            check(vkEnumerateDeviceExtensionProperties(candidate, nullptr, &extension_count, extensions.data()));
            bool compatible = true;
            for (const char* required : device_ext) {
                compatible &= std::any_of(extensions.begin(), extensions.end(),
                    [required](const auto& supported) {
                        return std::strcmp(required, supported.extensionName) == 0;
                    });
            }
            if (!compatible) continue;
            uint32_t count = 0;
            vkGetPhysicalDeviceQueueFamilyProperties(candidate, &count, nullptr);
            std::vector<VkQueueFamilyProperties> families(count);
            vkGetPhysicalDeviceQueueFamilyProperties(candidate, &count, families.data());
            uint32_t index = 0;
            while (index < count && (families[index].queueFlags &
                   (VK_QUEUE_GRAPHICS_BIT | VK_QUEUE_COMPUTE_BIT)) !=
                   (VK_QUEUE_GRAPHICS_BIT | VK_QUEUE_COMPUTE_BIT)) ++index;
            if (index == count) continue;
            if (!physical || (!discrete && props.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU)) {
                physical = candidate;
                family = index;
                explicit_subgroup_stages = explicit_size;
                discrete = props.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU;
            }
        }
        require(physical, "No Vulkan 1.3 GPU supports the Imp shader extensions and 32-lane subgroups");
        VkPhysicalDeviceProperties selected{};
        vkGetPhysicalDeviceProperties(physical, &selected);
        std::cout << "device=" << selected.deviceName << '\n';
        VkPhysicalDeviceVulkan13Features f{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_3_FEATURES};
        f.subgroupSizeControl=explicit_subgroup_stages != 0;f.shaderDemoteToHelperInvocation=VK_TRUE;f.dynamicRendering=VK_TRUE; f.synchronization2=VK_TRUE;
VkPhysicalDeviceVulkan12Features bda{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_2_FEATURES};bda.bufferDeviceAddress=VK_TRUE;bda.shaderOutputLayer=VK_TRUE;bda.shaderInt8=VK_TRUE;bda.uniformAndStorageBuffer8BitAccess=VK_TRUE;VkPhysicalDeviceVulkan11Features f11{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_1_FEATURES};f11.uniformAndStorageBuffer16BitAccess=VK_TRUE;bda.pNext=&f11;f.pNext=&bda; VkPhysicalDeviceRobustness2FeaturesEXT robust{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ROBUSTNESS_2_FEATURES_EXT};robust.nullDescriptor=VK_TRUE;robust.robustBufferAccess2=VK_TRUE;robust.robustImageAccess2=VK_TRUE;f11.pNext=&robust; VkPhysicalDeviceDepthClipEnableFeaturesEXT depthclip{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DEPTH_CLIP_ENABLE_FEATURES_EXT};depthclip.depthClipEnable=VK_TRUE;robust.pNext=&depthclip;VkPhysicalDeviceWorkgroupMemoryExplicitLayoutFeaturesKHR wg{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_WORKGROUP_MEMORY_EXPLICIT_LAYOUT_FEATURES_KHR};wg.workgroupMemoryExplicitLayout=VK_TRUE;wg.workgroupMemoryExplicitLayout16BitAccess=VK_TRUE;depthclip.pNext=&wg;
        VkPhysicalDeviceFragmentShaderBarycentricFeaturesKHR barycentric{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADER_BARYCENTRIC_FEATURES_KHR};
        barycentric.fragmentShaderBarycentric=VK_TRUE; wg.pNext=&barycentric;
        float priority=1; VkDeviceQueueCreateInfo qi{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
        qi.queueFamilyIndex=family; qi.queueCount=1; qi.pQueuePriorities=&priority;
        VkDeviceCreateInfo di{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO}; di.pNext=&f; di.queueCreateInfoCount=1; di.pQueueCreateInfos=&qi;
        VkPhysicalDeviceFeatures features{};features.robustBufferAccess=VK_TRUE;features.shaderStorageImageReadWithoutFormat=VK_TRUE;features.shaderStorageImageWriteWithoutFormat=VK_TRUE;features.depthClamp=VK_TRUE;features.shaderInt16=VK_TRUE;features.shaderInt64=VK_TRUE;features.textureCompressionBC=VK_TRUE;features.shaderImageGatherExtended=VK_TRUE;features.vertexPipelineStoresAndAtomics=VK_TRUE;features.fragmentStoresAndAtomics=VK_TRUE;di.pEnabledFeatures=&features;
        di.enabledExtensionCount = uint32_t(std::size(device_ext));
        di.ppEnabledExtensionNames = device_ext;
        const VkResult device_result = vkCreateDevice(physical, &di, nullptr, &device);
        if (device_result == VK_ERROR_FEATURE_NOT_PRESENT) {
            throw std::runtime_error(std::string(selected.deviceName) +
                " does not expose all Vulkan features required by the Dreams Imp shaders");
        }
        check(device_result);
        vkGetDeviceQueue(device, family, 0, &queue);
        vkGetPhysicalDeviceMemoryProperties(physical,&memory);
        VkCommandPoolCreateInfo pi{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
        pi.flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT; pi.queueFamilyIndex=family;
        check(vkCreateCommandPool(device,&pi,nullptr,&pool));
        VkCommandBufferAllocateInfo ai{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
        ai.commandPool=pool; ai.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY; ai.commandBufferCount=2;
        check(vkAllocateCommandBuffers(device,&ai,commands));
    }
    uint32_t memory_type(uint32_t mask,VkMemoryPropertyFlags flags=0) {
        for(uint32_t i=0;i<memory.memoryTypeCount;i++)
            if((mask&(1u<<i)) && (memory.memoryTypes[i].propertyFlags&flags)==flags) return i;
        throw std::runtime_error("memory type unavailable");
    }
    void begin(unsigned i) {
        check(vkResetCommandBuffer(commands[i],0));
        VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO}; check(vkBeginCommandBuffer(commands[i],&bi));
    }
    void submit(unsigned start,unsigned count,bool wait) {
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO}; si.commandBufferCount=count; si.pCommandBuffers=commands+start;
        check(vkQueueSubmit(queue,1,&si,VK_NULL_HANDLE)); if(wait) check(vkQueueWaitIdle(queue));
    }
    ~Context() {
        vkDestroyCommandPool(device,pool,nullptr); vkDestroyDevice(device,nullptr);
        if (messenger) destroy_debug(instance,messenger,nullptr);
        vkDestroyInstance(instance,nullptr);
    }
};





#include <filesystem>
static VkShaderModule load_module(Context& c,const std::string& path){
    std::ifstream f(path,std::ios::binary|std::ios::ate);require(bool(f),"shader missing");
    std::vector<uint32_t> data(size_t(f.tellg())/4);f.seekg(0);f.read((char*)data.data(),data.size()*4);
    VkShaderModuleCreateInfo i{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};i.codeSize=data.size()*4;i.pCode=data.data();
    VkShaderModule result;check(vkCreateShaderModule(c.device,&i,nullptr,&result));return result;
}
