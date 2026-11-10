#version 450
#extension GL_EXT_shader_explicit_arithmetic_types_int8 : require
#extension GL_EXT_shader_8bit_storage : require
#extension GL_EXT_shader_explicit_arithmetic_types_int16 : require
#extension GL_EXT_shader_16bit_storage : require
#if defined(GL_ARB_gpu_shader_int64)
#extension GL_ARB_gpu_shader_int64 : require
#else
#error No extension available for 64-bit integers.
#endif
#extension GL_EXT_buffer_reference2 : require
#extension GL_KHR_shader_subgroup_ballot : require
#extension GL_KHR_shader_subgroup_basic : require
#extension GL_ARB_shader_viewport_layer_array : require

layout(buffer_reference) buffer uintPointer;

struct full_result_i32x2
{
    int _m0;
    int _m1;
};

struct full_result_u32x2
{
    uint _m0;
    uint _m1;
};

struct frexp_result_f32
{
    float _m0;
    int _m1;
};

uint _147;
uint _148;
uint _149;
uint _150;
uint _151;
uint _152;
uint _153;
uint _154;
uint _155;

layout(buffer_reference, buffer_reference_align = 4) buffer uintPointer
{
    uint value;
};

layout(set = 0, binding = 10, std430) readonly buffer ssbo_5
{
    uint data[];
} ssbo_5_1;

layout(set = 0, binding = 11, std430) readonly buffer clip_planes
{
    float data[];
} clip_planes_1;

layout(set = 0, binding = 18, std430) readonly buffer srt_flatbuf
{
    uint data[];
} srt_flatbuf_1;

layout(set = 0, binding = 13, std430) buffer bda_pagetable
{
    uint64_t data[];
} bda_pagetable_1;

layout(set = 0, binding = 19, std430) buffer fault_buffer
{
    uint data[];
} fault_buffer_1;

layout(push_constant, std430) uniform AuxData
{
    float xoffset;
    float yoffset;
    float xscale;
    float yscale;
    uvec4 ud_regs0;
    uvec4 ud_regs1;
    uvec4 ud_regs2;
    uvec4 ud_regs3;
    uvec4 buf_offsets0;
    uvec4 buf_offsets1;
    uvec2 buf_offsets2;
    uvec2 host_data;
} push_data;

layout(location = 0) out vec4 out_attr0;
layout(location = 1) out vec4 out_attr1;
layout(location = 2) out vec4 out_attr2;
layout(location = 3) out vec4 out_attr3;
layout(location = 4) out vec4 out_attr4;
layout(location = 5) out vec4 out_attr5;
layout(location = 6) out vec4 out_attr6;

uint64_t get_bda_pointer(uint64_t _84)
{
    uint _90 = uint(_84 >> 14ul);
    uint64_t _92 = bda_pagetable_1.data[_90];
    uint64_t _104;
    if (_92 == 0ul)
    {
        uint _95 = _90 >> 5u;
        fault_buffer_1.data[_95] |= (1u << (_90 & 31u));
        _104 = 0ul;
    }
    else
    {
        _104 = _92 + (_84 & 16383ul);
    }
    return _104;
}

uint read_const_dynamic(uvec2 _107, uint _108)
{
    uint64_t _124 = get_bda_pointer((uint64_t(_107.x) | (uint64_t(_107.y) << 32u)) + uint64_t(_108 << 2u));
    uint _128;
    if (_124 != 0ul)
    {
        _128 = uintPointer(_124).value;
    }
    else
    {
        _128 = 0u;
    }
    return _128;
}

void main()
{
    precise float _208 = uintBitsToFloat(srt_flatbuf_1.data[60u]) * uintBitsToFloat(srt_flatbuf_1.data[31u]);
    precise float _211 = uintBitsToFloat(srt_flatbuf_1.data[29u]) * uintBitsToFloat(srt_flatbuf_1.data[61u]);
    precise float _215 = uintBitsToFloat(srt_flatbuf_1.data[30u]) * (-uintBitsToFloat(srt_flatbuf_1.data[61u]));
    precise float _216 = _215 + _208;
    precise float _219 = uintBitsToFloat(srt_flatbuf_1.data[59u]) * uintBitsToFloat(srt_flatbuf_1.data[30u]);
    precise float _222 = uintBitsToFloat(srt_flatbuf_1.data[59u]) * uintBitsToFloat(srt_flatbuf_1.data[32u]);
    precise float _223 = _222 + _216;
    precise float _227 = uintBitsToFloat(srt_flatbuf_1.data[31u]) * (-uintBitsToFloat(srt_flatbuf_1.data[59u]));
    precise float _228 = _227 + _211;
    precise float _231 = uintBitsToFloat(srt_flatbuf_1.data[60u]) * uintBitsToFloat(srt_flatbuf_1.data[32u]);
    precise float _232 = _231 + _228;
    precise float _235 = uintBitsToFloat(srt_flatbuf_1.data[59u]) * uintBitsToFloat(srt_flatbuf_1.data[29u]);
    precise float _238 = uintBitsToFloat(srt_flatbuf_1.data[29u]) * uintBitsToFloat(srt_flatbuf_1.data[62u]);
    precise float _239 = _238 + _223;
    precise float _244 = uintBitsToFloat(srt_flatbuf_1.data[29u]) * (-uintBitsToFloat(srt_flatbuf_1.data[60u]));
    precise float _245 = _244 + _219;
    precise float _246 = _239 * _239;
    precise float _249 = uintBitsToFloat(srt_flatbuf_1.data[61u]) * uintBitsToFloat(srt_flatbuf_1.data[32u]);
    precise float _250 = _249 + _245;
    precise float _253 = uintBitsToFloat(srt_flatbuf_1.data[62u]) * uintBitsToFloat(srt_flatbuf_1.data[30u]);
    precise float _254 = _253 + _232;
    precise float _258 = uintBitsToFloat(srt_flatbuf_1.data[60u]) * uintBitsToFloat(srt_flatbuf_1.data[30u]);
    precise float _259 = _258 + _235;
    precise float _260 = _254 * _254;
    precise float _261 = _260 + _246;
    precise float _264 = uintBitsToFloat(srt_flatbuf_1.data[62u]) * uintBitsToFloat(srt_flatbuf_1.data[31u]);
    precise float _265 = _264 + _250;
    precise float _269 = uintBitsToFloat(srt_flatbuf_1.data[61u]) * uintBitsToFloat(srt_flatbuf_1.data[31u]);
    precise float _270 = _269 + _259;
    precise float _271 = _265 * _265;
    precise float _272 = _271 + _261;
    precise float _276 = uintBitsToFloat(srt_flatbuf_1.data[62u]) * uintBitsToFloat(srt_flatbuf_1.data[32u]);
    precise float _277 = _276 + (-_270);
    precise float _279 = _277 * _277;
    precise float _280 = _279 + _272;
    bool _281 = isinf(_280);
    uvec4 _283 = subgroupBallot(0.0 == _280);
    precise float _287 = (-1.0) + _280;
    uvec4 _292 = subgroupBallot(abs(_287) <= 4.9999999873762135393917560577393e-07);
    uint _298 = gl_SubgroupInvocationID & 63u;
    uint _307 = gl_SubgroupInvocationID & 63u;
    bool _314 = (((((_307 >= 32u) ? _292.y : _292.x) >> (_307 & 31u)) & 1u) != 0u) || ((((((_298 >= 32u) ? _283.y : _283.x) >> (_298 & 31u)) & 1u) != 0u) || _281);
    uint _335;
    uint _336;
    uint _337;
    uint _338;
    if (_314)
    {
        uvec4 _317 = subgroupBallot(0.0 == _280);
        uint _322 = gl_SubgroupInvocationID & 63u;
        bool _329 = (((((_322 >= 32u) ? _317.y : _317.x) >> (_322 & 31u)) & 1u) != 0u) || (0u != uint(_281));
        _335 = _329 ? 1065353216u : floatBitsToUint(_277);
        _336 = _329 ? 0u : floatBitsToUint(_265);
        _337 = _329 ? 0u : floatBitsToUint(_254);
        _338 = _329 ? 0u : floatBitsToUint(_239);
    }
    else
    {
        _335 = _152;
        _336 = _153;
        _337 = _154;
        _338 = _155;
    }
    uint _348;
    uint _349;
    uint _350;
    uint _351;
    if (!_314)
    {
        float _339 = inversesqrt(_280);
        precise float _340 = _339 * _239;
        precise float _342 = _339 * _254;
        precise float _344 = _339 * _265;
        precise float _346 = _339 * _277;
        _348 = floatBitsToUint(_346);
        _349 = floatBitsToUint(_344);
        _350 = floatBitsToUint(_342);
        _351 = floatBitsToUint(_340);
    }
    else
    {
        _348 = _335;
        _349 = _336;
        _350 = _337;
        _351 = _338;
    }
    precise float _391 = uintBitsToFloat(srt_flatbuf_1.data[68u]) * uintBitsToFloat(srt_flatbuf_1.data[39u]);
    precise float _394 = uintBitsToFloat(srt_flatbuf_1.data[37u]) * uintBitsToFloat(srt_flatbuf_1.data[69u]);
    precise float _398 = uintBitsToFloat(srt_flatbuf_1.data[38u]) * (-uintBitsToFloat(srt_flatbuf_1.data[69u]));
    precise float _399 = _398 + _391;
    precise float _402 = uintBitsToFloat(srt_flatbuf_1.data[67u]) * uintBitsToFloat(srt_flatbuf_1.data[38u]);
    precise float _405 = uintBitsToFloat(srt_flatbuf_1.data[67u]) * uintBitsToFloat(srt_flatbuf_1.data[40u]);
    precise float _406 = _405 + _399;
    precise float _410 = uintBitsToFloat(srt_flatbuf_1.data[39u]) * (-uintBitsToFloat(srt_flatbuf_1.data[67u]));
    precise float _411 = _410 + _394;
    precise float _414 = uintBitsToFloat(srt_flatbuf_1.data[68u]) * uintBitsToFloat(srt_flatbuf_1.data[40u]);
    precise float _415 = _414 + _411;
    precise float _418 = uintBitsToFloat(srt_flatbuf_1.data[67u]) * uintBitsToFloat(srt_flatbuf_1.data[37u]);
    precise float _421 = uintBitsToFloat(srt_flatbuf_1.data[37u]) * uintBitsToFloat(srt_flatbuf_1.data[70u]);
    precise float _422 = _421 + _406;
    precise float _427 = uintBitsToFloat(srt_flatbuf_1.data[37u]) * (-uintBitsToFloat(srt_flatbuf_1.data[68u]));
    precise float _428 = _427 + _402;
    precise float _429 = _422 * _422;
    precise float _432 = uintBitsToFloat(srt_flatbuf_1.data[69u]) * uintBitsToFloat(srt_flatbuf_1.data[40u]);
    precise float _433 = _432 + _428;
    precise float _436 = uintBitsToFloat(srt_flatbuf_1.data[70u]) * uintBitsToFloat(srt_flatbuf_1.data[38u]);
    precise float _437 = _436 + _415;
    precise float _441 = uintBitsToFloat(srt_flatbuf_1.data[68u]) * uintBitsToFloat(srt_flatbuf_1.data[38u]);
    precise float _442 = _441 + _418;
    precise float _443 = _437 * _437;
    precise float _444 = _443 + _429;
    precise float _447 = uintBitsToFloat(srt_flatbuf_1.data[70u]) * uintBitsToFloat(srt_flatbuf_1.data[39u]);
    precise float _448 = _447 + _433;
    precise float _452 = uintBitsToFloat(srt_flatbuf_1.data[69u]) * uintBitsToFloat(srt_flatbuf_1.data[39u]);
    precise float _453 = _452 + _442;
    precise float _454 = _448 * _448;
    precise float _455 = _454 + _444;
    precise float _459 = uintBitsToFloat(srt_flatbuf_1.data[70u]) * uintBitsToFloat(srt_flatbuf_1.data[40u]);
    precise float _460 = _459 + (-_453);
    precise float _462 = _460 * _460;
    precise float _463 = _462 + _455;
    bool _464 = isinf(_463);
    uvec4 _466 = subgroupBallot(0.0 == _463);
    precise float _469 = (-1.0) + _463;
    uvec4 _472 = subgroupBallot(abs(_469) <= 4.9999999873762135393917560577393e-07);
    uint _477 = gl_SubgroupInvocationID & 63u;
    uint _486 = gl_SubgroupInvocationID & 63u;
    bool _493 = (((((_486 >= 32u) ? _472.y : _472.x) >> (_486 & 31u)) & 1u) != 0u) || ((((((_477 >= 32u) ? _466.y : _466.x) >> (_477 & 31u)) & 1u) != 0u) || _464);
    uint _513;
    uint _514;
    uint _515;
    uint _516;
    if (_493)
    {
        uvec4 _496 = subgroupBallot(0.0 == _463);
        uint _501 = gl_SubgroupInvocationID & 63u;
        bool _508 = (((((_501 >= 32u) ? _496.y : _496.x) >> (_501 & 31u)) & 1u) != 0u) || (0u != uint(_464));
        _513 = _508 ? 1065353216u : floatBitsToUint(_460);
        _514 = _508 ? 0u : floatBitsToUint(_437);
        _515 = _508 ? 0u : floatBitsToUint(_422);
        _516 = _508 ? 0u : floatBitsToUint(_448);
    }
    else
    {
        _513 = _147;
        _514 = _148;
        _515 = _149;
        _516 = _150;
    }
    uint _526;
    uint _527;
    uint _528;
    uint _529;
    if (!_493)
    {
        float _517 = inversesqrt(_463);
        precise float _518 = _517 * _422;
        precise float _520 = _517 * _437;
        precise float _522 = _517 * _448;
        precise float _524 = _517 * _460;
        _526 = floatBitsToUint(_524);
        _527 = floatBitsToUint(_520);
        _528 = floatBitsToUint(_518);
        _529 = floatBitsToUint(_522);
    }
    else
    {
        _526 = _513;
        _527 = _514;
        _528 = _515;
        _529 = _516;
    }
    bool _532 = ((push_data.ud_regs1.x >> 0u) & 1u) == 1u;
    uint _542;
    if (_532)
    {
        _542 = floatBitsToUint(-uintBitsToFloat(srt_flatbuf_1.data[53u]));
    }
    else
    {
        _542 = _151;
    }
    uint _546;
    if (!_532)
    {
        _546 = srt_flatbuf_1.data[53u];
    }
    else
    {
        _546 = _542;
    }
    uint _552 = srt_flatbuf_1.data[24u];
    float _633 = float(1u & uint(gl_VertexIndex));
    precise float _635 = 2.0 * _633;
    precise float _636 = _635 + (-1.0);
    float _637 = float(uint(gl_VertexIndex) >> 1u);
    precise float _638 = 2.0 * _637;
    precise float _639 = _638 + (-1.0);
    uint _640 = _552 + uint(gl_InstanceIndex);
    uint _642 = (_640 * 34u) + 3u;
    uvec3 _651 = uvec3(ssbo_5_1.data[_642], ssbo_5_1.data[_642 + 1u], ssbo_5_1.data[_642 + 2u]);
    uint _652 = _651.x;
    uint _653 = _651.y;
    uint _654 = _651.z;
    uint _657 = (_640 * 34u) + 6u;
    uvec3 _666 = uvec3(ssbo_5_1.data[_657], ssbo_5_1.data[_657 + 1u], ssbo_5_1.data[_657 + 2u]);
    uint _670 = _640 * 34u;
    uvec3 _679 = uvec3(ssbo_5_1.data[_670], ssbo_5_1.data[_670 + 1u], ssbo_5_1.data[_670 + 2u]);
    uint _685 = (_640 * 34u) + 9u;
    uvec3 _694 = uvec3(ssbo_5_1.data[_685], ssbo_5_1.data[_685 + 1u], ssbo_5_1.data[_685 + 2u]);
    uint _700 = (_640 * 34u) + 15u;
    uvec3 _709 = uvec3(ssbo_5_1.data[_700], ssbo_5_1.data[_700 + 1u], ssbo_5_1.data[_700 + 2u]);
    uint _714 = (_640 * 34u) + 18u;
    uvec3 _723 = uvec3(ssbo_5_1.data[_714], ssbo_5_1.data[_714 + 1u], ssbo_5_1.data[_714 + 2u]);
    uint _729 = (_640 * 34u) + 12u;
    uvec3 _738 = uvec3(ssbo_5_1.data[_729], ssbo_5_1.data[_729 + 1u], ssbo_5_1.data[_729 + 2u]);
    uint _744 = (_640 * 34u) + 21u;
    uvec3 _753 = uvec3(ssbo_5_1.data[_744], ssbo_5_1.data[_744 + 1u], ssbo_5_1.data[_744 + 2u]);
    uint _758 = _640 + 4321u;
    uint _762 = ((61u ^ (_758 >> 16u)) ^ _758) * 9u;
    uint _766 = ((_762 >> 4u) ^ _762) * 668265261u;
    precise float _773 = 0.00999999977648258209228515625 * float(bitfieldExtract((_766 >> 15u) ^ _766, int(8u), int(8u)));
    precise float _776 = uintBitsToFloat(srt_flatbuf_1.data[50u]) * 12.3999996185302734375;
    precise float _777 = _776 + _773;
    precise float _779 = 0.15915493667125701904296875 * _777;
    precise float _781 = uintBitsToFloat(srt_flatbuf_1.data[49u]) * 12.3999996185302734375;
    precise float _782 = _781 + _773;
    precise float _784 = 0.15915493667125701904296875 * _782;
    precise float _792 = uintBitsToFloat(srt_flatbuf_1.data[25u]) * uintBitsToFloat(srt_flatbuf_1.data[61u]);
    precise float _795 = uintBitsToFloat(srt_flatbuf_1.data[60u]) * uintBitsToFloat(srt_flatbuf_1.data[27u]);
    precise float _799 = uintBitsToFloat(srt_flatbuf_1.data[27u]) * (-uintBitsToFloat(srt_flatbuf_1.data[59u]));
    precise float _800 = _799 + _792;
    precise float _803 = uintBitsToFloat(srt_flatbuf_1.data[59u]) * uintBitsToFloat(srt_flatbuf_1.data[26u]);
    precise float _807 = uintBitsToFloat(srt_flatbuf_1.data[26u]) * (-uintBitsToFloat(srt_flatbuf_1.data[61u]));
    precise float _808 = _807 + _795;
    precise float _811 = uintBitsToFloat(srt_flatbuf_1.data[68u]) * uintBitsToFloat(srt_flatbuf_1.data[35u]);
    precise float _814 = uintBitsToFloat(srt_flatbuf_1.data[67u]) * uintBitsToFloat(srt_flatbuf_1.data[34u]);
    precise float _818 = uintBitsToFloat(srt_flatbuf_1.data[33u]) * (-uintBitsToFloat(srt_flatbuf_1.data[68u]));
    precise float _819 = _818 + _814;
    precise float _822 = uintBitsToFloat(srt_flatbuf_1.data[35u]) * uintBitsToFloat(srt_flatbuf_1.data[70u]);
    precise float _823 = _822 + _819;
    precise float _827 = uintBitsToFloat(srt_flatbuf_1.data[34u]) * (-uintBitsToFloat(srt_flatbuf_1.data[69u]));
    precise float _828 = _827 + _811;
    precise float _831 = uintBitsToFloat(srt_flatbuf_1.data[33u]) * uintBitsToFloat(srt_flatbuf_1.data[70u]);
    precise float _832 = _831 + _828;
    precise float _835 = uintBitsToFloat(srt_flatbuf_1.data[33u]) * uintBitsToFloat(srt_flatbuf_1.data[69u]);
    precise float _839 = uintBitsToFloat(srt_flatbuf_1.data[35u]) * (-uintBitsToFloat(srt_flatbuf_1.data[67u]));
    precise float _840 = _839 + _835;
    precise float _843 = uintBitsToFloat(srt_flatbuf_1.data[26u]) * uintBitsToFloat(srt_flatbuf_1.data[62u]);
    precise float _844 = _843 + _800;
    precise float _848 = uintBitsToFloat(srt_flatbuf_1.data[25u]) * (-uintBitsToFloat(srt_flatbuf_1.data[60u]));
    precise float _849 = _848 + _803;
    precise float _852 = uintBitsToFloat(srt_flatbuf_1.data[25u]) * uintBitsToFloat(srt_flatbuf_1.data[62u]);
    precise float _853 = _852 + _808;
    precise float _855 = uintBitsToFloat(srt_flatbuf_1.data[61u]) * _844;
    precise float _858 = uintBitsToFloat(srt_flatbuf_1.data[27u]) * uintBitsToFloat(srt_flatbuf_1.data[62u]);
    precise float _859 = _858 + _849;
    precise float _861 = uintBitsToFloat(srt_flatbuf_1.data[60u]) * _853;
    precise float _864 = uintBitsToFloat(srt_flatbuf_1.data[34u]) * uintBitsToFloat(srt_flatbuf_1.data[70u]);
    precise float _865 = _864 + _840;
    precise float _868 = uintBitsToFloat(srt_flatbuf_1.data[60u]) * (-_859);
    precise float _869 = _868 + _855;
    precise float _871 = uintBitsToFloat(srt_flatbuf_1.data[69u]) * _865;
    precise float _873 = uintBitsToFloat(srt_flatbuf_1.data[68u]) * _832;
    precise float _875 = uintBitsToFloat(srt_flatbuf_1.data[59u]) * _859;
    precise float _878 = uintBitsToFloat(srt_flatbuf_1.data[59u]) * (-_844);
    precise float _879 = _878 + _861;
    precise float _882 = (-2.0) * _869;
    precise float _883 = _882 + uintBitsToFloat(srt_flatbuf_1.data[25u]);
    precise float _885 = (-2.0) * _879;
    precise float _886 = _885 + uintBitsToFloat(srt_flatbuf_1.data[27u]);
    precise float _889 = uintBitsToFloat(srt_flatbuf_1.data[68u]) * (-_823);
    precise float _890 = _889 + _871;
    precise float _892 = uintBitsToFloat(srt_flatbuf_1.data[67u]) * _823;
    precise float _895 = uintBitsToFloat(srt_flatbuf_1.data[69u]) * (-_832);
    precise float _896 = _895 + _892;
    precise float _899 = uintBitsToFloat(srt_flatbuf_1.data[67u]) * (-_865);
    precise float _900 = _899 + _873;
    precise float _903 = uintBitsToFloat(srt_flatbuf_1.data[61u]) * (-_853);
    precise float _904 = _903 + _875;
    precise float _907 = uintBitsToFloat(srt_flatbuf_1.data[58u]) * _883;
    precise float _908 = _907 + uintBitsToFloat(srt_flatbuf_1.data[55u]);
    precise float _911 = uintBitsToFloat(srt_flatbuf_1.data[28u]) * uintBitsToFloat(srt_flatbuf_1.data[58u]);
    precise float _913 = (-2.0) * _900;
    precise float _914 = _913 + uintBitsToFloat(srt_flatbuf_1.data[35u]);
    precise float _916 = (-2.0) * _904;
    precise float _917 = _916 + uintBitsToFloat(srt_flatbuf_1.data[26u]);
    precise float _920 = uintBitsToFloat(srt_flatbuf_1.data[58u]) * _886;
    precise float _921 = _920 + uintBitsToFloat(srt_flatbuf_1.data[57u]);
    precise float _923 = (-2.0) * _890;
    precise float _924 = _923 + uintBitsToFloat(srt_flatbuf_1.data[33u]);
    precise float _927 = uintBitsToFloat(srt_flatbuf_1.data[66u]) * _924;
    precise float _928 = _927 + uintBitsToFloat(srt_flatbuf_1.data[63u]);
    precise float _931 = uintBitsToFloat(srt_flatbuf_1.data[36u]) * uintBitsToFloat(srt_flatbuf_1.data[66u]);
    precise float _934 = uintBitsToFloat(srt_flatbuf_1.data[66u]) * _914;
    precise float _935 = _934 + uintBitsToFloat(srt_flatbuf_1.data[65u]);
    precise float _937 = (-2.0) * _896;
    precise float _938 = _937 + uintBitsToFloat(srt_flatbuf_1.data[34u]);
    precise float _941 = uintBitsToFloat(srt_flatbuf_1.data[58u]) * _917;
    precise float _942 = _941 + uintBitsToFloat(srt_flatbuf_1.data[56u]);
    precise float _945 = uintBitsToFloat(srt_flatbuf_1.data[66u]) * _938;
    precise float _946 = _945 + uintBitsToFloat(srt_flatbuf_1.data[64u]);
    precise float _950 = uintBitsToFloat(_652) * uintBitsToFloat(_652);
    precise float _953 = uintBitsToFloat(_653) * uintBitsToFloat(_653);
    precise float _954 = _953 + _950;
    precise float _957 = uintBitsToFloat(_654) * uintBitsToFloat(_654);
    precise float _958 = _957 + _954;
    precise float _960 = sqrt(_958) * 2.0;
    precise float _964 = uintBitsToFloat(srt_flatbuf_1.data[51u]) * clamp(_960, 0.0, 1.0);
    precise float _967 = (-0.5) * _964;
    precise float _968 = _967 + uintBitsToFloat(srt_flatbuf_1.data[51u]);
    precise float _969 = sin(6.283185482025146484375 * fract(_779)) * _968;
    precise float _972 = uintBitsToFloat(_679.x) * _636;
    precise float _973 = _972 + uintBitsToFloat(_694.x);
    precise float _974 = sin(6.283185482025146484375 * fract(_784)) * _968;
    precise float _977 = _969 * uintBitsToFloat(_666.x);
    precise float _978 = _977 + uintBitsToFloat(_652);
    precise float _981 = _969 * uintBitsToFloat(_666.z);
    precise float _982 = _981 + uintBitsToFloat(_654);
    precise float _985 = _636 * uintBitsToFloat(_679.z);
    precise float _986 = _985 + uintBitsToFloat(_694.z);
    precise float _987 = _639 * _982;
    precise float _988 = _987 + _986;
    precise float _991 = uintBitsToFloat(_723.x) * _974;
    precise float _992 = _991 + uintBitsToFloat(_709.x);
    precise float _995 = uintBitsToFloat(_738.x) * _636;
    precise float _996 = _995 + uintBitsToFloat(_753.x);
    precise float _999 = uintBitsToFloat(_738.z) * _636;
    precise float _1000 = _999 + uintBitsToFloat(_753.z);
    precise float _1001 = _978 * _639;
    precise float _1002 = _1001 + _973;
    precise float _1005 = _969 * uintBitsToFloat(_666.y);
    precise float _1006 = _1005 + uintBitsToFloat(_653);
    precise float _1009 = _636 * uintBitsToFloat(_679.y);
    precise float _1010 = _1009 + uintBitsToFloat(_694.y);
    precise float _1013 = _974 * uintBitsToFloat(_723.z);
    precise float _1014 = _1013 + uintBitsToFloat(_709.z);
    precise float _1016 = uintBitsToFloat(_349) * _1002;
    precise float _1017 = _639 * _1006;
    precise float _1018 = _1017 + _1010;
    precise float _1020 = uintBitsToFloat(_350) * _988;
    precise float _1021 = _639 * _1014;
    precise float _1022 = _1021 + _1000;
    precise float _1025 = uintBitsToFloat(_738.y) * _636;
    precise float _1026 = _1025 + uintBitsToFloat(_753.y);
    precise float _1027 = _992 * _639;
    precise float _1028 = _1027 + _996;
    precise float _1031 = _974 * uintBitsToFloat(_723.y);
    precise float _1032 = _1031 + uintBitsToFloat(_709.y);
    precise float _1034 = uintBitsToFloat(_351) * _1018;
    precise float _1037 = (-uintBitsToFloat(_349)) * _1018;
    precise float _1038 = _1037 + _1020;
    precise float _1040 = uintBitsToFloat(_529) * _1028;
    precise float _1041 = _639 * _1032;
    precise float _1042 = _1041 + _1026;
    precise float _1044 = uintBitsToFloat(_527) * _1022;
    precise float _1047 = _988 * (-uintBitsToFloat(_351));
    precise float _1048 = _1047 + _1016;
    precise float _1050 = uintBitsToFloat(_348) * _1018;
    precise float _1051 = _1050 + _1048;
    precise float _1053 = uintBitsToFloat(_528) * _1042;
    precise float _1056 = _1002 * (-uintBitsToFloat(_350));
    precise float _1057 = _1056 + _1034;
    precise float _1059 = _1002 * uintBitsToFloat(_348);
    precise float _1060 = _1059 + _1038;
    precise float _1063 = _1022 * (-uintBitsToFloat(_528));
    precise float _1064 = _1063 + _1040;
    precise float _1067 = _1042 * (-uintBitsToFloat(_529));
    precise float _1068 = _1067 + _1044;
    precise float _1070 = uintBitsToFloat(_349) * _1051;
    precise float _1072 = uintBitsToFloat(_348) * _988;
    precise float _1073 = _1072 + _1057;
    precise float _1075 = uintBitsToFloat(_350) * _1060;
    precise float _1077 = uintBitsToFloat(_526) * _1028;
    precise float _1078 = _1077 + _1068;
    precise float _1080 = _1042 * uintBitsToFloat(_526);
    precise float _1081 = _1080 + _1064;
    precise float _1084 = _1028 * (-uintBitsToFloat(_527));
    precise float _1085 = _1084 + _1053;
    precise float _1087 = uintBitsToFloat(_529) * _1081;
    precise float _1089 = uintBitsToFloat(_527) * _1078;
    precise float _1091 = uintBitsToFloat(_351) * _1073;
    precise float _1094 = (-_1073) * uintBitsToFloat(_350);
    precise float _1095 = _1094 + _1070;
    precise float _1098 = (-_1051) * uintBitsToFloat(_351);
    precise float _1099 = _1098 + _1075;
    precise float _1101 = uintBitsToFloat(_526) * _1022;
    precise float _1102 = _1101 + _1085;
    precise float _1103 = (-2.0) * _1095;
    precise float _1104 = _1103 + _1002;
    precise float _1105 = (-2.0) * _1099;
    precise float _1106 = _1105 + _988;
    precise float _1108 = uintBitsToFloat(_528) * _1102;
    precise float _1111 = (-_1102) * uintBitsToFloat(_527);
    precise float _1112 = _1111 + _1087;
    precise float _1115 = (-_1081) * uintBitsToFloat(_528);
    precise float _1116 = _1115 + _1089;
    precise float _1119 = (-_1060) * uintBitsToFloat(_349);
    precise float _1120 = _1119 + _1091;
    precise float _1121 = _911 * _1104;
    precise float _1122 = _1121 + _908;
    precise float _1123 = _911 * _1106;
    precise float _1124 = _1123 + _921;
    precise float _1125 = (-2.0) * _1120;
    precise float _1126 = _1125 + _1018;
    precise float _1127 = (-2.0) * _1112;
    precise float _1128 = _1127 + _1028;
    precise float _1129 = (-2.0) * _1116;
    precise float _1130 = _1129 + _1022;
    precise float _1133 = (-_1078) * uintBitsToFloat(_529);
    precise float _1134 = _1133 + _1108;
    precise float _1136 = uintBitsToFloat(_546) + _1122;
    float _1137 = 1.0 / _1124;
    precise float _1138 = _911 * _1126;
    precise float _1139 = _1138 + _942;
    precise float _1140 = _1128 * _931;
    precise float _1141 = _1140 + _928;
    precise float _1142 = _1130 * _931;
    precise float _1143 = _1142 + _935;
    precise float _1144 = (-2.0) * _1134;
    precise float _1145 = _1144 + _1042;
    precise float _1146 = _1137 * _1136;
    precise float _1148 = uintBitsToFloat(_546) + _1141;
    float _1149 = 1.0 / _1143;
    precise float _1150 = _1137 * _1139;
    precise float _1151 = _1145 * _931;
    precise float _1152 = _1151 + _946;
    precise float _1154 = _1149 * _1148;
    precise float _1155 = _1154 + (-_1146);
    precise float _1158 = _1149 * _1152;
    precise float _1159 = _1158 + (-_1150);
    precise float _1161 = _1149 * _1148;
    precise float _1162 = _1149 * _1152;
    uint _1216;
    uint _1217;
    if (0u != srt_flatbuf_1.data[54u])
    {
        precise float _1198 = uintBitsToFloat(srt_flatbuf_1.data[41u]) * _1146;
        precise float _1199 = _1198 + uintBitsToFloat(srt_flatbuf_1.data[43u]);
        precise float _1202 = uintBitsToFloat(srt_flatbuf_1.data[42u]) * _1150;
        precise float _1203 = _1202 + uintBitsToFloat(srt_flatbuf_1.data[44u]);
        precise float _1205 = uintBitsToFloat(srt_flatbuf_1.data[47u]) - _1199;
        precise float _1207 = uintBitsToFloat(srt_flatbuf_1.data[48u]) - _1203;
        precise float _1209 = uintBitsToFloat(srt_flatbuf_1.data[45u]) * _1161;
        precise float _1210 = _1209 + _1205;
        precise float _1213 = uintBitsToFloat(srt_flatbuf_1.data[46u]) * _1162;
        precise float _1214 = _1213 + _1207;
        _1216 = floatBitsToUint(_1214);
        _1217 = floatBitsToUint(_1210);
    }
    else
    {
        _1216 = floatBitsToUint(_1159);
        _1217 = floatBitsToUint(_1155);
    }
    uint _1219 = (_640 * 34u) + 31u;
    uint _1221 = ssbo_5_1.data[_1219];
    uint _1224 = ssbo_5_1.data[_1219 + 1u];
    uint _1227 = ssbo_5_1.data[_1219 + 2u];
    uvec3 _1228 = uvec3(_1221, _1224, _1227);
    uint _1229 = _1228.x;
    uint _1230 = _1228.y;
    uint _1233 = (_640 * 34u) + 27u;
    uint _1235 = ssbo_5_1.data[_1233];
    uint _1238 = ssbo_5_1.data[_1233 + 1u];
    uint _1241 = ssbo_5_1.data[_1233 + 2u];
    uvec3 _1242 = uvec3(_1235, _1238, _1241);
    uint _1246 = push_data.ud_regs1.x << 6u;
    uint _1251 = (_1246 + 388u) >> 2u;
    uvec2 _1252 = uvec2(push_data.ud_regs0.z, push_data.ud_regs0.w);
    uint _1253 = read_const_dynamic(_1252, _1251);
    uint _1255 = read_const_dynamic(_1252, _1251 + 1u);
    uint _1257 = read_const_dynamic(_1252, _1251 + 2u);
    uint _1259 = read_const_dynamic(_1252, _1251 + 3u);
    uint _1260 = (_1246 + 340u) >> 2u;
    uvec2 _1261 = uvec2(push_data.ud_regs0.z, push_data.ud_regs0.w);
    uint _1262 = read_const_dynamic(_1261, _1260);
    uint _1264 = read_const_dynamic(_1261, _1260 + 1u);
    uint _1266 = read_const_dynamic(_1261, _1260 + 2u);
    uint _1268 = read_const_dynamic(_1261, _1260 + 3u);
    uint _1271 = (_1246 + 356u) >> 2u;
    uvec2 _1272 = uvec2(push_data.ud_regs0.z, push_data.ud_regs0.w);
    uint _1273 = read_const_dynamic(_1272, _1271);
    uint _1275 = read_const_dynamic(_1272, _1271 + 1u);
    uint _1277 = read_const_dynamic(_1272, _1271 + 2u);
    uint _1279 = read_const_dynamic(_1272, _1271 + 3u);
    uint _1282 = (_1246 + 372u) >> 2u;
    uvec2 _1283 = uvec2(push_data.ud_regs0.z, push_data.ud_regs0.w);
    uint _1284 = read_const_dynamic(_1283, _1282);
    uint _1286 = read_const_dynamic(_1283, _1282 + 1u);
    uint _1288 = read_const_dynamic(_1283, _1282 + 2u);
    uint _1290 = read_const_dynamic(_1283, _1282 + 3u);
    uint _1292 = _640 + 12345u;
    precise float _1304 = (-uintBitsToFloat(_546)) + (-_908);
    precise float _1307 = (-uintBitsToFloat(_349)) * _1304;
    precise float _1309 = uintBitsToFloat(_351) * _942;
    precise float _1311 = uintBitsToFloat(_350) * _921;
    precise float _1314 = (-uintBitsToFloat(_351)) * _921;
    precise float _1315 = _1314 + _1307;
    uint _1316 = ((61u ^ (_1292 >> 16u)) ^ _1292) * 9u;
    precise float _1318 = _1304 * uintBitsToFloat(_350);
    precise float _1319 = _1318 + _1309;
    precise float _1322 = _942 * (-uintBitsToFloat(_349));
    precise float _1323 = _1322 + _1311;
    precise float _1325 = uintBitsToFloat(_348) * _1304;
    precise float _1326 = _1325 + _1323;
    precise float _1330 = uintBitsToFloat(_348) * (-_942);
    precise float _1331 = _1330 + _1315;
    precise float _1334 = uintBitsToFloat(_348) * (-_921);
    precise float _1335 = _1334 + _1319;
    precise float _1338 = (-uintBitsToFloat(_349)) * _1331;
    precise float _1341 = (-uintBitsToFloat(_351)) * _1335;
    precise float _1344 = (-uintBitsToFloat(_350)) * _1326;
    precise float _1346 = _1335 * uintBitsToFloat(_350);
    precise float _1347 = _1346 + _1338;
    precise float _1349 = _1326 * uintBitsToFloat(_349);
    precise float _1350 = _1349 + _1341;
    precise float _1352 = _1331 * uintBitsToFloat(_351);
    precise float _1353 = _1352 + _1344;
    float _1354 = 1.0 / _911;
    precise float _1357 = uintBitsToFloat(_1262) * _1136;
    precise float _1358 = _1357 + uintBitsToFloat(_1253);
    precise float _1361 = _1136 * uintBitsToFloat(_1268);
    precise float _1362 = _1361 + uintBitsToFloat(_1259);
    precise float _1365 = _1136 * uintBitsToFloat(_1266);
    precise float _1366 = _1365 + uintBitsToFloat(_1257);
    precise float _1369 = uintBitsToFloat(_1264) * _1136;
    precise float _1370 = _1369 + uintBitsToFloat(_1255);
    precise float _1372 = uintBitsToFloat(_1273) * _1139;
    precise float _1373 = _1372 + _1358;
    precise float _1375 = uintBitsToFloat(_1279) * _1139;
    precise float _1376 = _1375 + _1362;
    precise float _1378 = uintBitsToFloat(_1277) * _1139;
    precise float _1379 = _1378 + _1366;
    precise float _1381 = uintBitsToFloat(_1275) * _1139;
    precise float _1382 = _1381 + _1370;
    precise float _1384 = uintBitsToFloat(_1284) * _1124;
    precise float _1385 = _1384 + _1373;
    precise float _1387 = _1124 * uintBitsToFloat(_1290);
    precise float _1388 = _1387 + _1376;
    precise float _1390 = uintBitsToFloat(_1288) * _1124;
    precise float _1391 = _1390 + _1379;
    precise float _1393 = uintBitsToFloat(_1286) * _1124;
    precise float _1394 = _1393 + _1382;
    gl_Layer = int(floatBitsToUint(uintBitsToFloat(push_data.ud_regs1.x)));
    gl_Position.x = _1385;
    gl_Position.y = _1394;
    gl_Position.z = _1391;
    gl_Position.w = _1388;
    uint _1402 = ((_1316 >> 4u) ^ _1316) * 668265261u;
    precise float _1404 = (-2.0) * _1350;
    precise float _1405 = _1404 + (-_942);
    precise float _1407 = (-2.0) * _1353;
    precise float _1408 = _1407 + (-_921);
    precise float _1410 = (-2.0) * _1347;
    precise float _1411 = _1410 + _1304;
    precise float _1412 = _1354 * _1411;
    precise float _1413 = _1354 * _1405;
    precise float _1414 = _1354 * _1408;
    precise float _1416 = 1.0 - _637;
    precise float _1419 = uintBitsToFloat(srt_flatbuf_1.data[52u]) * uintBitsToFloat(_1217);
    precise float _1422 = uintBitsToFloat(srt_flatbuf_1.data[52u]) * uintBitsToFloat(_1216);
    precise float _1426 = 0.0039215688593685626983642578125 * float(bitfieldExtract(_1229, int(0u), int(8u)));
    out_attr6.x = _1412;
    out_attr6.y = _1413;
    out_attr6.z = _1414;
    out_attr6.w = 0.0;
    out_attr5.x = uintBitsToFloat((_1402 >> 15u) ^ _1402);
    out_attr5.y = uintBitsToFloat(_1229);
    out_attr5.z = uintBitsToFloat(_1230);
    out_attr5.w = 0.0;
    out_attr4.x = uintBitsToFloat(_1242.x);
    out_attr4.y = uintBitsToFloat(_1242.y);
    out_attr4.z = uintBitsToFloat(_1242.z);
    out_attr4.w = _1426;
    out_attr3.x = _633;
    out_attr3.y = _1416;
    out_attr3.z = float(bitfieldExtract(_1230, int(24u), int(8u)));
    out_attr3.w = 0.0;
    out_attr2.x = 0.0;
    out_attr2.y = 0.0;
    out_attr2.z = 0.0;
    out_attr2.w = uintBitsToFloat(_1228.z);
    out_attr1.x = _1002;
    out_attr1.y = _1018;
    out_attr1.z = _988;
    out_attr1.w = 0.0;
    out_attr0.x = _1419;
    out_attr0.y = _1422;
    out_attr0.z = 0.0;
    out_attr0.w = 0.0;
}

