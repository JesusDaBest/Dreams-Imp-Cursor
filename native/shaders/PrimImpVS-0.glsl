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

uint _148;
uint _149;
uint _150;
uint _151;
uint _152;
uint _153;
uint _154;
uint _155;
uint _156;

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

layout(set = 0, binding = 12, std430) readonly buffer srt_flatbuf
{
    uint data[];
} srt_flatbuf_1;

layout(set = 0, binding = 13, std430) buffer bda_pagetable
{
    uint64_t data[];
} bda_pagetable_1;

layout(set = 0, binding = 14, std430) buffer fault_buffer
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

uint64_t get_bda_pointer(uint64_t _85)
{
    uint _91 = uint(_85 >> 14ul);
    uint64_t _93 = bda_pagetable_1.data[_91];
    uint64_t _105;
    if (_93 == 0ul)
    {
        uint _96 = _91 >> 5u;
        fault_buffer_1.data[_96] |= (1u << (_91 & 31u));
        _105 = 0ul;
    }
    else
    {
        _105 = _93 + (_85 & 16383ul);
    }
    return _105;
}

uint read_const_dynamic(uvec2 _108, uint _109)
{
    uint64_t _125 = get_bda_pointer((uint64_t(_108.x) | (uint64_t(_108.y) << 32u)) + uint64_t(_109 << 2u));
    uint _129;
    if (_125 != 0ul)
    {
        _129 = uintPointer(_125).value;
    }
    else
    {
        _129 = 0u;
    }
    return _129;
}

void main()
{
    precise float _209 = uintBitsToFloat(srt_flatbuf_1.data[60u]) * uintBitsToFloat(srt_flatbuf_1.data[31u]);
    precise float _212 = uintBitsToFloat(srt_flatbuf_1.data[29u]) * uintBitsToFloat(srt_flatbuf_1.data[61u]);
    precise float _216 = uintBitsToFloat(srt_flatbuf_1.data[30u]) * (-uintBitsToFloat(srt_flatbuf_1.data[61u]));
    precise float _217 = _216 + _209;
    precise float _220 = uintBitsToFloat(srt_flatbuf_1.data[59u]) * uintBitsToFloat(srt_flatbuf_1.data[30u]);
    precise float _223 = uintBitsToFloat(srt_flatbuf_1.data[59u]) * uintBitsToFloat(srt_flatbuf_1.data[32u]);
    precise float _224 = _223 + _217;
    precise float _228 = uintBitsToFloat(srt_flatbuf_1.data[31u]) * (-uintBitsToFloat(srt_flatbuf_1.data[59u]));
    precise float _229 = _228 + _212;
    precise float _232 = uintBitsToFloat(srt_flatbuf_1.data[60u]) * uintBitsToFloat(srt_flatbuf_1.data[32u]);
    precise float _233 = _232 + _229;
    precise float _236 = uintBitsToFloat(srt_flatbuf_1.data[59u]) * uintBitsToFloat(srt_flatbuf_1.data[29u]);
    precise float _239 = uintBitsToFloat(srt_flatbuf_1.data[29u]) * uintBitsToFloat(srt_flatbuf_1.data[62u]);
    precise float _240 = _239 + _224;
    precise float _244 = uintBitsToFloat(srt_flatbuf_1.data[29u]) * (-uintBitsToFloat(srt_flatbuf_1.data[60u]));
    precise float _245 = _244 + _220;
    precise float _246 = _240 * _240;
    precise float _249 = uintBitsToFloat(srt_flatbuf_1.data[61u]) * uintBitsToFloat(srt_flatbuf_1.data[32u]);
    precise float _250 = _249 + _245;
    precise float _253 = uintBitsToFloat(srt_flatbuf_1.data[62u]) * uintBitsToFloat(srt_flatbuf_1.data[30u]);
    precise float _254 = _253 + _233;
    precise float _257 = uintBitsToFloat(srt_flatbuf_1.data[60u]) * uintBitsToFloat(srt_flatbuf_1.data[30u]);
    precise float _258 = _257 + _236;
    precise float _259 = _254 * _254;
    precise float _260 = _259 + _246;
    precise float _263 = uintBitsToFloat(srt_flatbuf_1.data[62u]) * uintBitsToFloat(srt_flatbuf_1.data[31u]);
    precise float _264 = _263 + _250;
    precise float _267 = uintBitsToFloat(srt_flatbuf_1.data[61u]) * uintBitsToFloat(srt_flatbuf_1.data[31u]);
    precise float _268 = _267 + _258;
    precise float _269 = _264 * _264;
    precise float _270 = _269 + _260;
    precise float _274 = uintBitsToFloat(srt_flatbuf_1.data[62u]) * uintBitsToFloat(srt_flatbuf_1.data[32u]);
    precise float _275 = _274 + (-_268);
    precise float _276 = _275 * _275;
    precise float _277 = _276 + _270;
    bool _278 = isinf(_277);
    uvec4 _280 = subgroupBallot(0.0 == _277);
    precise float _284 = (-1.0) + _277;
    uvec4 _289 = subgroupBallot(abs(_284) <= 4.9999999873762135393917560577393e-07);
    uint _297 = gl_SubgroupInvocationID & 63u;
    uint _306 = gl_SubgroupInvocationID & 63u;
    bool _313 = (((((_306 >= 32u) ? _289.y : _289.x) >> (_306 & 31u)) & 1u) != 0u) || ((((((_297 >= 32u) ? _280.y : _280.x) >> (_297 & 31u)) & 1u) != 0u) || _278);
    uint _338;
    uint _339;
    uint _340;
    uint _341;
    if (_313)
    {
        uvec4 _316 = subgroupBallot(0.0 == _277);
        uint _321 = gl_SubgroupInvocationID & 63u;
        bool _328 = (((((_321 >= 32u) ? _316.y : _316.x) >> (_321 & 31u)) & 1u) != 0u) || (0u != floatBitsToUint(_278 ? 1.4012984643248170709237295832899e-45 : 0.0));
        _338 = floatBitsToUint(_328 ? 1.0 : _275);
        _339 = floatBitsToUint(_328 ? 0.0 : _264);
        _340 = floatBitsToUint(_328 ? 0.0 : _254);
        _341 = floatBitsToUint(_328 ? 0.0 : _240);
    }
    else
    {
        _338 = _153;
        _339 = _154;
        _340 = _155;
        _341 = _156;
    }
    uint _351;
    uint _352;
    uint _353;
    uint _354;
    if (!_313)
    {
        float _342 = inversesqrt(_277);
        precise float _343 = _342 * _240;
        precise float _345 = _342 * _254;
        precise float _347 = _342 * _264;
        precise float _349 = _342 * _275;
        _351 = floatBitsToUint(_349);
        _352 = floatBitsToUint(_347);
        _353 = floatBitsToUint(_345);
        _354 = floatBitsToUint(_343);
    }
    else
    {
        _351 = _338;
        _352 = _339;
        _353 = _340;
        _354 = _341;
    }
    precise float _394 = uintBitsToFloat(srt_flatbuf_1.data[68u]) * uintBitsToFloat(srt_flatbuf_1.data[39u]);
    precise float _397 = uintBitsToFloat(srt_flatbuf_1.data[37u]) * uintBitsToFloat(srt_flatbuf_1.data[69u]);
    precise float _401 = uintBitsToFloat(srt_flatbuf_1.data[38u]) * (-uintBitsToFloat(srt_flatbuf_1.data[69u]));
    precise float _402 = _401 + _394;
    precise float _405 = uintBitsToFloat(srt_flatbuf_1.data[67u]) * uintBitsToFloat(srt_flatbuf_1.data[38u]);
    precise float _408 = uintBitsToFloat(srt_flatbuf_1.data[67u]) * uintBitsToFloat(srt_flatbuf_1.data[40u]);
    precise float _409 = _408 + _402;
    precise float _413 = uintBitsToFloat(srt_flatbuf_1.data[39u]) * (-uintBitsToFloat(srt_flatbuf_1.data[67u]));
    precise float _414 = _413 + _397;
    precise float _417 = uintBitsToFloat(srt_flatbuf_1.data[68u]) * uintBitsToFloat(srt_flatbuf_1.data[40u]);
    precise float _418 = _417 + _414;
    precise float _421 = uintBitsToFloat(srt_flatbuf_1.data[67u]) * uintBitsToFloat(srt_flatbuf_1.data[37u]);
    precise float _424 = uintBitsToFloat(srt_flatbuf_1.data[37u]) * uintBitsToFloat(srt_flatbuf_1.data[70u]);
    precise float _425 = _424 + _409;
    precise float _429 = uintBitsToFloat(srt_flatbuf_1.data[37u]) * (-uintBitsToFloat(srt_flatbuf_1.data[68u]));
    precise float _430 = _429 + _405;
    precise float _431 = _425 * _425;
    precise float _434 = uintBitsToFloat(srt_flatbuf_1.data[69u]) * uintBitsToFloat(srt_flatbuf_1.data[40u]);
    precise float _435 = _434 + _430;
    precise float _438 = uintBitsToFloat(srt_flatbuf_1.data[70u]) * uintBitsToFloat(srt_flatbuf_1.data[38u]);
    precise float _439 = _438 + _418;
    precise float _442 = uintBitsToFloat(srt_flatbuf_1.data[68u]) * uintBitsToFloat(srt_flatbuf_1.data[38u]);
    precise float _443 = _442 + _421;
    precise float _444 = _439 * _439;
    precise float _445 = _444 + _431;
    precise float _448 = uintBitsToFloat(srt_flatbuf_1.data[70u]) * uintBitsToFloat(srt_flatbuf_1.data[39u]);
    precise float _449 = _448 + _435;
    precise float _452 = uintBitsToFloat(srt_flatbuf_1.data[69u]) * uintBitsToFloat(srt_flatbuf_1.data[39u]);
    precise float _453 = _452 + _443;
    precise float _454 = _449 * _449;
    precise float _455 = _454 + _445;
    precise float _459 = uintBitsToFloat(srt_flatbuf_1.data[70u]) * uintBitsToFloat(srt_flatbuf_1.data[40u]);
    precise float _460 = _459 + (-_453);
    precise float _461 = _460 * _460;
    precise float _462 = _461 + _455;
    bool _463 = isinf(_462);
    uvec4 _465 = subgroupBallot(0.0 == _462);
    precise float _468 = (-1.0) + _462;
    uvec4 _471 = subgroupBallot(abs(_468) <= 4.9999999873762135393917560577393e-07);
    uint _477 = gl_SubgroupInvocationID & 63u;
    uint _486 = gl_SubgroupInvocationID & 63u;
    bool _493 = (((((_486 >= 32u) ? _471.y : _471.x) >> (_486 & 31u)) & 1u) != 0u) || ((((((_477 >= 32u) ? _465.y : _465.x) >> (_477 & 31u)) & 1u) != 0u) || _463);
    uint _517;
    uint _518;
    uint _519;
    uint _520;
    if (_493)
    {
        uvec4 _496 = subgroupBallot(0.0 == _462);
        uint _501 = gl_SubgroupInvocationID & 63u;
        bool _508 = (((((_501 >= 32u) ? _496.y : _496.x) >> (_501 & 31u)) & 1u) != 0u) || (0u != floatBitsToUint(_463 ? 1.4012984643248170709237295832899e-45 : 0.0));
        _517 = floatBitsToUint(_508 ? 1.0 : _460);
        _518 = floatBitsToUint(_508 ? 0.0 : _439);
        _519 = floatBitsToUint(_508 ? 0.0 : _425);
        _520 = floatBitsToUint(_508 ? 0.0 : _449);
    }
    else
    {
        _517 = _148;
        _518 = _149;
        _519 = _150;
        _520 = _151;
    }
    uint _530;
    uint _531;
    uint _532;
    uint _533;
    if (!_493)
    {
        float _521 = inversesqrt(_462);
        precise float _522 = _521 * _425;
        precise float _524 = _521 * _439;
        precise float _526 = _521 * _449;
        precise float _528 = _521 * _460;
        _530 = floatBitsToUint(_528);
        _531 = floatBitsToUint(_524);
        _532 = floatBitsToUint(_522);
        _533 = floatBitsToUint(_526);
    }
    else
    {
        _530 = _517;
        _531 = _518;
        _532 = _519;
        _533 = _520;
    }
    bool _536 = ((push_data.ud_regs1.x >> 0u) & 1u) == 1u;
    uint _546;
    if (_536)
    {
        _546 = floatBitsToUint(-uintBitsToFloat(srt_flatbuf_1.data[53u]));
    }
    else
    {
        _546 = _152;
    }
    uint _550;
    if (!_536)
    {
        _550 = srt_flatbuf_1.data[53u];
    }
    else
    {
        _550 = _546;
    }
    uint _556 = srt_flatbuf_1.data[24u];
    float _637 = float(1u & uint(gl_VertexIndex));
    precise float _639 = 2.0 * _637;
    precise float _640 = _639 + (-1.0);
    float _641 = float(uint(gl_VertexIndex) >> 1u);
    precise float _642 = 2.0 * _641;
    precise float _643 = _642 + (-1.0);
    uint _644 = _556 + uint(gl_InstanceIndex);
    uint _646 = (_644 * 34u) + 3u;
    uvec3 _655 = uvec3(ssbo_5_1.data[_646], ssbo_5_1.data[_646 + 1u], ssbo_5_1.data[_646 + 2u]);
    uint _656 = _655.x;
    uint _657 = _655.y;
    uint _658 = _655.z;
    uint _661 = (_644 * 34u) + 6u;
    uvec3 _670 = uvec3(ssbo_5_1.data[_661], ssbo_5_1.data[_661 + 1u], ssbo_5_1.data[_661 + 2u]);
    uint _674 = _644 * 34u;
    uvec3 _683 = uvec3(ssbo_5_1.data[_674], ssbo_5_1.data[_674 + 1u], ssbo_5_1.data[_674 + 2u]);
    uint _689 = (_644 * 34u) + 9u;
    uvec3 _698 = uvec3(ssbo_5_1.data[_689], ssbo_5_1.data[_689 + 1u], ssbo_5_1.data[_689 + 2u]);
    uint _704 = (_644 * 34u) + 15u;
    uvec3 _713 = uvec3(ssbo_5_1.data[_704], ssbo_5_1.data[_704 + 1u], ssbo_5_1.data[_704 + 2u]);
    uint _718 = (_644 * 34u) + 18u;
    uvec3 _727 = uvec3(ssbo_5_1.data[_718], ssbo_5_1.data[_718 + 1u], ssbo_5_1.data[_718 + 2u]);
    uint _733 = (_644 * 34u) + 12u;
    uvec3 _742 = uvec3(ssbo_5_1.data[_733], ssbo_5_1.data[_733 + 1u], ssbo_5_1.data[_733 + 2u]);
    uint _748 = (_644 * 34u) + 21u;
    uvec3 _757 = uvec3(ssbo_5_1.data[_748], ssbo_5_1.data[_748 + 1u], ssbo_5_1.data[_748 + 2u]);
    uint _762 = _644 + 4321u;
    uint _766 = ((61u ^ (_762 >> 16u)) ^ _762) * 9u;
    uint _770 = ((_766 >> 4u) ^ _766) * 668265261u;
    precise float _777 = 0.00999999977648258209228515625 * float(bitfieldExtract((_770 >> 15u) ^ _770, int(8u), int(8u)));
    precise float _780 = uintBitsToFloat(srt_flatbuf_1.data[50u]) * 12.3999996185302734375;
    precise float _781 = _780 + _777;
    precise float _783 = 0.15915493667125701904296875 * _781;
    precise float _785 = uintBitsToFloat(srt_flatbuf_1.data[49u]) * 12.3999996185302734375;
    precise float _786 = _785 + _777;
    precise float _788 = 0.15915493667125701904296875 * _786;
    precise float _796 = uintBitsToFloat(srt_flatbuf_1.data[25u]) * uintBitsToFloat(srt_flatbuf_1.data[61u]);
    precise float _799 = uintBitsToFloat(srt_flatbuf_1.data[60u]) * uintBitsToFloat(srt_flatbuf_1.data[27u]);
    precise float _803 = uintBitsToFloat(srt_flatbuf_1.data[27u]) * (-uintBitsToFloat(srt_flatbuf_1.data[59u]));
    precise float _804 = _803 + _796;
    precise float _807 = uintBitsToFloat(srt_flatbuf_1.data[59u]) * uintBitsToFloat(srt_flatbuf_1.data[26u]);
    precise float _811 = uintBitsToFloat(srt_flatbuf_1.data[26u]) * (-uintBitsToFloat(srt_flatbuf_1.data[61u]));
    precise float _812 = _811 + _799;
    precise float _815 = uintBitsToFloat(srt_flatbuf_1.data[68u]) * uintBitsToFloat(srt_flatbuf_1.data[35u]);
    precise float _818 = uintBitsToFloat(srt_flatbuf_1.data[67u]) * uintBitsToFloat(srt_flatbuf_1.data[34u]);
    precise float _822 = uintBitsToFloat(srt_flatbuf_1.data[33u]) * (-uintBitsToFloat(srt_flatbuf_1.data[68u]));
    precise float _823 = _822 + _818;
    precise float _826 = uintBitsToFloat(srt_flatbuf_1.data[35u]) * uintBitsToFloat(srt_flatbuf_1.data[70u]);
    precise float _827 = _826 + _823;
    precise float _831 = uintBitsToFloat(srt_flatbuf_1.data[34u]) * (-uintBitsToFloat(srt_flatbuf_1.data[69u]));
    precise float _832 = _831 + _815;
    precise float _835 = uintBitsToFloat(srt_flatbuf_1.data[33u]) * uintBitsToFloat(srt_flatbuf_1.data[70u]);
    precise float _836 = _835 + _832;
    precise float _839 = uintBitsToFloat(srt_flatbuf_1.data[33u]) * uintBitsToFloat(srt_flatbuf_1.data[69u]);
    precise float _843 = uintBitsToFloat(srt_flatbuf_1.data[35u]) * (-uintBitsToFloat(srt_flatbuf_1.data[67u]));
    precise float _844 = _843 + _839;
    precise float _847 = uintBitsToFloat(srt_flatbuf_1.data[26u]) * uintBitsToFloat(srt_flatbuf_1.data[62u]);
    precise float _848 = _847 + _804;
    precise float _852 = uintBitsToFloat(srt_flatbuf_1.data[25u]) * (-uintBitsToFloat(srt_flatbuf_1.data[60u]));
    precise float _853 = _852 + _807;
    precise float _856 = uintBitsToFloat(srt_flatbuf_1.data[25u]) * uintBitsToFloat(srt_flatbuf_1.data[62u]);
    precise float _857 = _856 + _812;
    precise float _859 = uintBitsToFloat(srt_flatbuf_1.data[61u]) * _848;
    precise float _862 = uintBitsToFloat(srt_flatbuf_1.data[27u]) * uintBitsToFloat(srt_flatbuf_1.data[62u]);
    precise float _863 = _862 + _853;
    precise float _865 = uintBitsToFloat(srt_flatbuf_1.data[60u]) * _857;
    precise float _868 = uintBitsToFloat(srt_flatbuf_1.data[34u]) * uintBitsToFloat(srt_flatbuf_1.data[70u]);
    precise float _869 = _868 + _844;
    precise float _872 = uintBitsToFloat(srt_flatbuf_1.data[60u]) * (-_863);
    precise float _873 = _872 + _859;
    precise float _875 = uintBitsToFloat(srt_flatbuf_1.data[69u]) * _869;
    precise float _877 = uintBitsToFloat(srt_flatbuf_1.data[68u]) * _836;
    precise float _879 = uintBitsToFloat(srt_flatbuf_1.data[59u]) * _863;
    precise float _882 = uintBitsToFloat(srt_flatbuf_1.data[59u]) * (-_848);
    precise float _883 = _882 + _865;
    precise float _886 = (-2.0) * _873;
    precise float _887 = _886 + uintBitsToFloat(srt_flatbuf_1.data[25u]);
    precise float _889 = (-2.0) * _883;
    precise float _890 = _889 + uintBitsToFloat(srt_flatbuf_1.data[27u]);
    precise float _893 = uintBitsToFloat(srt_flatbuf_1.data[68u]) * (-_827);
    precise float _894 = _893 + _875;
    precise float _896 = uintBitsToFloat(srt_flatbuf_1.data[67u]) * _827;
    precise float _899 = uintBitsToFloat(srt_flatbuf_1.data[69u]) * (-_836);
    precise float _900 = _899 + _896;
    precise float _903 = uintBitsToFloat(srt_flatbuf_1.data[67u]) * (-_869);
    precise float _904 = _903 + _877;
    precise float _907 = uintBitsToFloat(srt_flatbuf_1.data[61u]) * (-_857);
    precise float _908 = _907 + _879;
    precise float _911 = uintBitsToFloat(srt_flatbuf_1.data[58u]) * _887;
    precise float _912 = _911 + uintBitsToFloat(srt_flatbuf_1.data[55u]);
    precise float _915 = uintBitsToFloat(srt_flatbuf_1.data[28u]) * uintBitsToFloat(srt_flatbuf_1.data[58u]);
    precise float _917 = (-2.0) * _904;
    precise float _918 = _917 + uintBitsToFloat(srt_flatbuf_1.data[35u]);
    precise float _920 = (-2.0) * _908;
    precise float _921 = _920 + uintBitsToFloat(srt_flatbuf_1.data[26u]);
    precise float _924 = uintBitsToFloat(srt_flatbuf_1.data[58u]) * _890;
    precise float _925 = _924 + uintBitsToFloat(srt_flatbuf_1.data[57u]);
    precise float _927 = (-2.0) * _894;
    precise float _928 = _927 + uintBitsToFloat(srt_flatbuf_1.data[33u]);
    precise float _931 = uintBitsToFloat(srt_flatbuf_1.data[66u]) * _928;
    precise float _932 = _931 + uintBitsToFloat(srt_flatbuf_1.data[63u]);
    precise float _935 = uintBitsToFloat(srt_flatbuf_1.data[36u]) * uintBitsToFloat(srt_flatbuf_1.data[66u]);
    precise float _938 = uintBitsToFloat(srt_flatbuf_1.data[66u]) * _918;
    precise float _939 = _938 + uintBitsToFloat(srt_flatbuf_1.data[65u]);
    precise float _941 = (-2.0) * _900;
    precise float _942 = _941 + uintBitsToFloat(srt_flatbuf_1.data[34u]);
    precise float _945 = uintBitsToFloat(srt_flatbuf_1.data[58u]) * _921;
    precise float _946 = _945 + uintBitsToFloat(srt_flatbuf_1.data[56u]);
    precise float _949 = uintBitsToFloat(srt_flatbuf_1.data[66u]) * _942;
    precise float _950 = _949 + uintBitsToFloat(srt_flatbuf_1.data[64u]);
    precise float _954 = uintBitsToFloat(_656) * uintBitsToFloat(_656);
    precise float _957 = uintBitsToFloat(_657) * uintBitsToFloat(_657);
    precise float _958 = _957 + _954;
    precise float _961 = uintBitsToFloat(_658) * uintBitsToFloat(_658);
    precise float _962 = _961 + _958;
    precise float _964 = sqrt(_962) * 2.0;
    precise float _967 = uintBitsToFloat(srt_flatbuf_1.data[51u]) * clamp(_964, 0.0, 1.0);
    precise float _970 = (-0.5) * _967;
    precise float _971 = _970 + uintBitsToFloat(srt_flatbuf_1.data[51u]);
    precise float _972 = sin(6.283185482025146484375 * fract(_783)) * _971;
    precise float _975 = uintBitsToFloat(_683.x) * _640;
    precise float _976 = _975 + uintBitsToFloat(_698.x);
    precise float _977 = sin(6.283185482025146484375 * fract(_788)) * _971;
    precise float _980 = _972 * uintBitsToFloat(_670.x);
    precise float _981 = _980 + uintBitsToFloat(_656);
    precise float _984 = _972 * uintBitsToFloat(_670.z);
    precise float _985 = _984 + uintBitsToFloat(_658);
    precise float _988 = _640 * uintBitsToFloat(_683.z);
    precise float _989 = _988 + uintBitsToFloat(_698.z);
    precise float _990 = _643 * _985;
    precise float _991 = _990 + _989;
    precise float _994 = uintBitsToFloat(_727.x) * _977;
    precise float _995 = _994 + uintBitsToFloat(_713.x);
    precise float _998 = uintBitsToFloat(_742.x) * _640;
    precise float _999 = _998 + uintBitsToFloat(_757.x);
    precise float _1002 = uintBitsToFloat(_742.z) * _640;
    precise float _1003 = _1002 + uintBitsToFloat(_757.z);
    precise float _1004 = _981 * _643;
    precise float _1005 = _1004 + _976;
    precise float _1008 = _972 * uintBitsToFloat(_670.y);
    precise float _1009 = _1008 + uintBitsToFloat(_657);
    precise float _1012 = _640 * uintBitsToFloat(_683.y);
    precise float _1013 = _1012 + uintBitsToFloat(_698.y);
    precise float _1016 = _977 * uintBitsToFloat(_727.z);
    precise float _1017 = _1016 + uintBitsToFloat(_713.z);
    precise float _1019 = uintBitsToFloat(_352) * _1005;
    precise float _1020 = _643 * _1009;
    precise float _1021 = _1020 + _1013;
    precise float _1023 = uintBitsToFloat(_353) * _991;
    precise float _1024 = _643 * _1017;
    precise float _1025 = _1024 + _1003;
    precise float _1028 = uintBitsToFloat(_742.y) * _640;
    precise float _1029 = _1028 + uintBitsToFloat(_757.y);
    precise float _1030 = _995 * _643;
    precise float _1031 = _1030 + _999;
    precise float _1034 = _977 * uintBitsToFloat(_727.y);
    precise float _1035 = _1034 + uintBitsToFloat(_713.y);
    precise float _1037 = uintBitsToFloat(_354) * _1021;
    precise float _1040 = (-uintBitsToFloat(_352)) * _1021;
    precise float _1041 = _1040 + _1023;
    precise float _1043 = uintBitsToFloat(_533) * _1031;
    precise float _1044 = _643 * _1035;
    precise float _1045 = _1044 + _1029;
    precise float _1047 = uintBitsToFloat(_531) * _1025;
    precise float _1050 = _991 * (-uintBitsToFloat(_354));
    precise float _1051 = _1050 + _1019;
    precise float _1053 = uintBitsToFloat(_351) * _1021;
    precise float _1054 = _1053 + _1051;
    precise float _1056 = uintBitsToFloat(_532) * _1045;
    precise float _1059 = _1005 * (-uintBitsToFloat(_353));
    precise float _1060 = _1059 + _1037;
    precise float _1062 = _1005 * uintBitsToFloat(_351);
    precise float _1063 = _1062 + _1041;
    precise float _1066 = _1025 * (-uintBitsToFloat(_532));
    precise float _1067 = _1066 + _1043;
    precise float _1070 = _1045 * (-uintBitsToFloat(_533));
    precise float _1071 = _1070 + _1047;
    precise float _1073 = uintBitsToFloat(_352) * _1054;
    precise float _1075 = uintBitsToFloat(_351) * _991;
    precise float _1076 = _1075 + _1060;
    precise float _1078 = uintBitsToFloat(_353) * _1063;
    precise float _1080 = uintBitsToFloat(_530) * _1031;
    precise float _1081 = _1080 + _1071;
    precise float _1083 = _1045 * uintBitsToFloat(_530);
    precise float _1084 = _1083 + _1067;
    precise float _1087 = _1031 * (-uintBitsToFloat(_531));
    precise float _1088 = _1087 + _1056;
    precise float _1090 = uintBitsToFloat(_533) * _1084;
    precise float _1092 = uintBitsToFloat(_531) * _1081;
    precise float _1094 = uintBitsToFloat(_354) * _1076;
    precise float _1097 = (-_1076) * uintBitsToFloat(_353);
    precise float _1098 = _1097 + _1073;
    precise float _1101 = (-_1054) * uintBitsToFloat(_354);
    precise float _1102 = _1101 + _1078;
    precise float _1104 = uintBitsToFloat(_530) * _1025;
    precise float _1105 = _1104 + _1088;
    precise float _1106 = (-2.0) * _1098;
    precise float _1107 = _1106 + _1005;
    precise float _1108 = (-2.0) * _1102;
    precise float _1109 = _1108 + _991;
    precise float _1111 = uintBitsToFloat(_532) * _1105;
    precise float _1114 = (-_1105) * uintBitsToFloat(_531);
    precise float _1115 = _1114 + _1090;
    precise float _1118 = (-_1084) * uintBitsToFloat(_532);
    precise float _1119 = _1118 + _1092;
    precise float _1122 = (-_1063) * uintBitsToFloat(_352);
    precise float _1123 = _1122 + _1094;
    precise float _1124 = _915 * _1107;
    precise float _1125 = _1124 + _912;
    precise float _1126 = _915 * _1109;
    precise float _1127 = _1126 + _925;
    precise float _1128 = (-2.0) * _1123;
    precise float _1129 = _1128 + _1021;
    precise float _1130 = (-2.0) * _1115;
    precise float _1131 = _1130 + _1031;
    precise float _1132 = (-2.0) * _1119;
    precise float _1133 = _1132 + _1025;
    precise float _1136 = (-_1081) * uintBitsToFloat(_533);
    precise float _1137 = _1136 + _1111;
    precise float _1139 = uintBitsToFloat(_550) + _1125;
    float _1140 = 1.0 / _1127;
    precise float _1141 = _915 * _1129;
    precise float _1142 = _1141 + _946;
    precise float _1143 = _1131 * _935;
    precise float _1144 = _1143 + _932;
    precise float _1145 = _1133 * _935;
    precise float _1146 = _1145 + _939;
    precise float _1147 = (-2.0) * _1137;
    precise float _1148 = _1147 + _1045;
    precise float _1149 = _1140 * _1139;
    precise float _1151 = uintBitsToFloat(_550) + _1144;
    float _1152 = 1.0 / _1146;
    precise float _1153 = _1140 * _1142;
    precise float _1154 = _1148 * _935;
    precise float _1155 = _1154 + _950;
    precise float _1157 = _1152 * _1151;
    precise float _1158 = _1157 + (-_1149);
    precise float _1161 = _1152 * _1155;
    precise float _1162 = _1161 + (-_1153);
    precise float _1164 = _1152 * _1151;
    precise float _1165 = _1152 * _1155;
    uint _1219;
    uint _1220;
    if (0u != srt_flatbuf_1.data[54u])
    {
        precise float _1201 = uintBitsToFloat(srt_flatbuf_1.data[41u]) * _1149;
        precise float _1202 = _1201 + uintBitsToFloat(srt_flatbuf_1.data[43u]);
        precise float _1205 = uintBitsToFloat(srt_flatbuf_1.data[42u]) * _1153;
        precise float _1206 = _1205 + uintBitsToFloat(srt_flatbuf_1.data[44u]);
        precise float _1208 = uintBitsToFloat(srt_flatbuf_1.data[47u]) - _1202;
        precise float _1210 = uintBitsToFloat(srt_flatbuf_1.data[48u]) - _1206;
        precise float _1212 = uintBitsToFloat(srt_flatbuf_1.data[45u]) * _1164;
        precise float _1213 = _1212 + _1208;
        precise float _1216 = uintBitsToFloat(srt_flatbuf_1.data[46u]) * _1165;
        precise float _1217 = _1216 + _1210;
        _1219 = floatBitsToUint(_1217);
        _1220 = floatBitsToUint(_1213);
    }
    else
    {
        _1219 = floatBitsToUint(_1162);
        _1220 = floatBitsToUint(_1158);
    }
    uint _1222 = (_644 * 34u) + 31u;
    uint _1224 = ssbo_5_1.data[_1222];
    uint _1227 = ssbo_5_1.data[_1222 + 1u];
    uint _1230 = ssbo_5_1.data[_1222 + 2u];
    uvec3 _1231 = uvec3(_1224, _1227, _1230);
    uint _1232 = _1231.x;
    uint _1233 = _1231.y;
    uint _1236 = (_644 * 34u) + 27u;
    uint _1238 = ssbo_5_1.data[_1236];
    uint _1241 = ssbo_5_1.data[_1236 + 1u];
    uint _1244 = ssbo_5_1.data[_1236 + 2u];
    uvec3 _1245 = uvec3(_1238, _1241, _1244);
    uint _1249 = push_data.ud_regs1.x << 6u;
    uint _1254 = (_1249 + 388u) >> 2u;
    uvec2 _1255 = uvec2(push_data.ud_regs0.z, push_data.ud_regs0.w);
    uint _1256 = read_const_dynamic(_1255, _1254);
    uint _1258 = read_const_dynamic(_1255, _1254 + 1u);
    uint _1260 = read_const_dynamic(_1255, _1254 + 2u);
    uint _1262 = read_const_dynamic(_1255, _1254 + 3u);
    uint _1263 = (_1249 + 340u) >> 2u;
    uvec2 _1264 = uvec2(push_data.ud_regs0.z, push_data.ud_regs0.w);
    uint _1265 = read_const_dynamic(_1264, _1263);
    uint _1267 = read_const_dynamic(_1264, _1263 + 1u);
    uint _1269 = read_const_dynamic(_1264, _1263 + 2u);
    uint _1271 = read_const_dynamic(_1264, _1263 + 3u);
    uint _1274 = (_1249 + 356u) >> 2u;
    uvec2 _1275 = uvec2(push_data.ud_regs0.z, push_data.ud_regs0.w);
    uint _1276 = read_const_dynamic(_1275, _1274);
    uint _1278 = read_const_dynamic(_1275, _1274 + 1u);
    uint _1280 = read_const_dynamic(_1275, _1274 + 2u);
    uint _1282 = read_const_dynamic(_1275, _1274 + 3u);
    uint _1285 = (_1249 + 372u) >> 2u;
    uvec2 _1286 = uvec2(push_data.ud_regs0.z, push_data.ud_regs0.w);
    uint _1287 = read_const_dynamic(_1286, _1285);
    uint _1289 = read_const_dynamic(_1286, _1285 + 1u);
    uint _1291 = read_const_dynamic(_1286, _1285 + 2u);
    uint _1293 = read_const_dynamic(_1286, _1285 + 3u);
    uint _1295 = _644 + 12345u;
    precise float _1307 = (-uintBitsToFloat(_550)) + (-_912);
    precise float _1310 = (-uintBitsToFloat(_352)) * _1307;
    precise float _1312 = uintBitsToFloat(_354) * _946;
    precise float _1314 = uintBitsToFloat(_353) * _925;
    precise float _1317 = (-uintBitsToFloat(_354)) * _925;
    precise float _1318 = _1317 + _1310;
    uint _1319 = ((61u ^ (_1295 >> 16u)) ^ _1295) * 9u;
    precise float _1321 = _1307 * uintBitsToFloat(_353);
    precise float _1322 = _1321 + _1312;
    precise float _1325 = _946 * (-uintBitsToFloat(_352));
    precise float _1326 = _1325 + _1314;
    precise float _1328 = uintBitsToFloat(_351) * _1307;
    precise float _1329 = _1328 + _1326;
    precise float _1333 = uintBitsToFloat(_351) * (-_946);
    precise float _1334 = _1333 + _1318;
    precise float _1337 = uintBitsToFloat(_351) * (-_925);
    precise float _1338 = _1337 + _1322;
    precise float _1341 = (-uintBitsToFloat(_352)) * _1334;
    precise float _1344 = (-uintBitsToFloat(_354)) * _1338;
    precise float _1347 = (-uintBitsToFloat(_353)) * _1329;
    precise float _1349 = _1338 * uintBitsToFloat(_353);
    precise float _1350 = _1349 + _1341;
    precise float _1352 = _1329 * uintBitsToFloat(_352);
    precise float _1353 = _1352 + _1344;
    precise float _1355 = _1334 * uintBitsToFloat(_354);
    precise float _1356 = _1355 + _1347;
    float _1357 = 1.0 / _915;
    precise float _1360 = uintBitsToFloat(_1265) * _1139;
    precise float _1361 = _1360 + uintBitsToFloat(_1256);
    precise float _1364 = _1139 * uintBitsToFloat(_1271);
    precise float _1365 = _1364 + uintBitsToFloat(_1262);
    precise float _1368 = _1139 * uintBitsToFloat(_1269);
    precise float _1369 = _1368 + uintBitsToFloat(_1260);
    precise float _1372 = uintBitsToFloat(_1267) * _1139;
    precise float _1373 = _1372 + uintBitsToFloat(_1258);
    precise float _1375 = uintBitsToFloat(_1276) * _1142;
    precise float _1376 = _1375 + _1361;
    precise float _1378 = uintBitsToFloat(_1282) * _1142;
    precise float _1379 = _1378 + _1365;
    precise float _1381 = uintBitsToFloat(_1280) * _1142;
    precise float _1382 = _1381 + _1369;
    precise float _1384 = uintBitsToFloat(_1278) * _1142;
    precise float _1385 = _1384 + _1373;
    precise float _1387 = uintBitsToFloat(_1287) * _1127;
    precise float _1388 = _1387 + _1376;
    precise float _1390 = _1127 * uintBitsToFloat(_1293);
    precise float _1391 = _1390 + _1379;
    precise float _1393 = uintBitsToFloat(_1291) * _1127;
    precise float _1394 = _1393 + _1382;
    precise float _1396 = uintBitsToFloat(_1289) * _1127;
    precise float _1397 = _1396 + _1385;
    gl_Layer = int(floatBitsToUint(uintBitsToFloat(push_data.ud_regs1.x)));
    gl_Position.x = _1388;
    gl_Position.y = _1397;
    gl_Position.z = _1394;
    gl_Position.w = _1391;
    uint _1405 = ((_1319 >> 4u) ^ _1319) * 668265261u;
    precise float _1407 = (-2.0) * _1353;
    precise float _1408 = _1407 + (-_946);
    precise float _1410 = (-2.0) * _1356;
    precise float _1411 = _1410 + (-_925);
    precise float _1413 = (-2.0) * _1350;
    precise float _1414 = _1413 + _1307;
    precise float _1415 = _1357 * _1414;
    precise float _1416 = _1357 * _1408;
    precise float _1417 = _1357 * _1411;
    precise float _1419 = 1.0 - _641;
    precise float _1422 = uintBitsToFloat(srt_flatbuf_1.data[52u]) * uintBitsToFloat(_1220);
    precise float _1425 = uintBitsToFloat(srt_flatbuf_1.data[52u]) * uintBitsToFloat(_1219);
    precise float _1429 = 0.0039215688593685626983642578125 * float(bitfieldExtract(_1232, int(0u), int(8u)));
    out_attr6.x = _1415;
    out_attr6.y = _1416;
    out_attr6.z = _1417;
    out_attr6.w = 0.0;
    out_attr5.x = uintBitsToFloat((_1405 >> 15u) ^ _1405);
    out_attr5.y = uintBitsToFloat(_1232);
    out_attr5.z = uintBitsToFloat(_1233);
    out_attr5.w = 0.0;
    out_attr4.x = uintBitsToFloat(_1245.x);
    out_attr4.y = uintBitsToFloat(_1245.y);
    out_attr4.z = uintBitsToFloat(_1245.z);
    out_attr4.w = _1429;
    out_attr3.x = _637;
    out_attr3.y = _1419;
    out_attr3.z = float(bitfieldExtract(_1233, int(24u), int(8u)));
    out_attr3.w = 0.0;
    out_attr2.x = 0.0;
    out_attr2.y = 0.0;
    out_attr2.z = 0.0;
    out_attr2.w = uintBitsToFloat(_1231.z);
    out_attr1.x = _1005;
    out_attr1.y = _1021;
    out_attr1.z = _991;
    out_attr1.w = 0.0;
    out_attr0.x = _1422;
    out_attr0.y = _1425;
    out_attr0.z = 0.0;
    out_attr0.w = 0.0;
}

