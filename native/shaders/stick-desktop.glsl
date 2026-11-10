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

layout(buffer_reference, buffer_reference_align = 4) buffer uintPointer
{
    uint value;
};

layout(set = 0, binding = 10, std430) readonly buffer ssbo_5
{
    uint data[];
} ssbo_5_1;

layout(set = 0, binding = 15, std430) readonly buffer ssbo_6
{
    uint data[];
} ssbo_6_1;

layout(set = 0, binding = 11, std430) readonly buffer clip_planes
{
    float data[];
} clip_planes_1;

layout(set = 0, binding = 16, std430) readonly buffer srt_flatbuf
{
    uint data[];
} srt_flatbuf_1;

layout(set = 0, binding = 13, std430) buffer bda_pagetable
{
    uint64_t data[];
} bda_pagetable_1;

layout(set = 0, binding = 17, std430) buffer fault_buffer
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
    uint _166 = srt_flatbuf_1.data[28u];
    uvec4 _172 = subgroupBallot(2u > uint(gl_VertexIndex));
    uint _173 = _172.x;
    uint _174 = _172.y;
    float _175 = float(1u & uint(gl_VertexIndex));
    precise float _178 = 2.0 * _175;
    precise float _180 = _178 + (-1.0);
    float _181 = float(uint(gl_VertexIndex) >> 1u);
    precise float _182 = 2.0 * _181;
    precise float _183 = _182 + (-1.0);
    uint _184 = _166 + uint(gl_InstanceIndex);
    uint _186 = _184 * 34u;
    uvec3 _195 = uvec3(ssbo_5_1.data[_186], ssbo_5_1.data[_186 + 1u], ssbo_5_1.data[_186 + 2u]);
    uint _201 = (_184 * 34u) + 9u;
    uvec3 _210 = uvec3(ssbo_5_1.data[_201], ssbo_5_1.data[_201 + 1u], ssbo_5_1.data[_201 + 2u]);
    uint _216 = (_184 * 34u) + 12u;
    uvec3 _225 = uvec3(ssbo_5_1.data[_216], ssbo_5_1.data[_216 + 1u], ssbo_5_1.data[_216 + 2u]);
    uint _231 = (_184 * 34u) + 21u;
    uvec3 _240 = uvec3(ssbo_5_1.data[_231], ssbo_5_1.data[_231 + 1u], ssbo_5_1.data[_231 + 2u]);
    uint _245 = (_184 * 34u) + 3u;
    uvec3 _254 = uvec3(ssbo_5_1.data[_245], ssbo_5_1.data[_245 + 1u], ssbo_5_1.data[_245 + 2u]);
    uint _260 = (_184 * 34u) + 15u;
    uvec3 _269 = uvec3(ssbo_5_1.data[_260], ssbo_5_1.data[_260 + 1u], ssbo_5_1.data[_260 + 2u]);
    uint _275 = (_184 * 34u) + 33u;
    uvec4 _281 = subgroupBallot((srt_flatbuf_1.data[29u] + 4294967295u) > _184);
    uvec4 _285 = subgroupBallot(_166 < _184);
    uint _290 = gl_SubgroupInvocationID & 63u;
    uint _298 = gl_SubgroupInvocationID & 63u;
    uvec4 _306 = subgroupBallot((((((_298 >= 32u) ? _281.y : _281.x) >> (_298 & 31u)) & 1u) != 0u) || (((((_290 >= 32u) ? _174 : _173) >> (_290 & 31u)) & 1u) != 0u));
    uint _310 = gl_SubgroupInvocationID & 63u;
    uint _318 = gl_SubgroupInvocationID & 63u;
    uint _328 = gl_SubgroupInvocationID & 63u;
    bool _335 = ((((((_310 >= 32u) ? _285.y : _285.x) >> (_310 & 31u)) & 1u) != 0u) || (!(((((_318 >= 32u) ? _174 : _173) >> (_318 & 31u)) & 1u) != 0u))) && (((((_328 >= 32u) ? _306.y : _306.x) >> (_328 & 31u)) & 1u) != 0u);
    precise float _338 = _180 * uintBitsToFloat(_195.x);
    precise float _339 = _338 + uintBitsToFloat(_210.x);
    precise float _342 = _180 * uintBitsToFloat(_195.y);
    precise float _343 = _342 + uintBitsToFloat(_210.y);
    precise float _346 = _180 * uintBitsToFloat(_195.z);
    precise float _347 = _346 + uintBitsToFloat(_210.z);
    precise float _350 = _180 * uintBitsToFloat(_225.x);
    precise float _351 = _350 + uintBitsToFloat(_240.x);
    precise float _354 = _180 * uintBitsToFloat(_225.y);
    precise float _355 = _354 + uintBitsToFloat(_240.y);
    precise float _358 = _180 * uintBitsToFloat(_225.z);
    precise float _359 = _358 + uintBitsToFloat(_240.z);
    precise float _361 = uintBitsToFloat(_254.x) * _183;
    precise float _362 = _361 + _339;
    precise float _365 = uintBitsToFloat(_254.y) * _183;
    precise float _366 = _365 + _343;
    precise float _369 = uintBitsToFloat(_254.z) * _183;
    precise float _370 = _369 + _347;
    precise float _373 = uintBitsToFloat(_269.x) * _183;
    precise float _374 = _373 + _351;
    precise float _377 = uintBitsToFloat(_269.y) * _183;
    precise float _378 = _377 + _355;
    precise float _381 = uintBitsToFloat(_269.z) * _183;
    precise float _382 = _381 + _359;
    uvec4 _384 = subgroupBallot(true);
    uint _385 = _384.x;
    uint _386 = _384.y;
    uint _548;
    uint _549;
    uint _550;
    uint _551;
    uint _552;
    uint _553;
    uint _554;
    if (_335)
    {
        uint _390 = ((_335 && (2u > uint(gl_VertexIndex))) ? 4294967295u : 1u) + _184;
        uint _392 = (_390 * 34u) + 21u;
        uvec3 _401 = uvec3(ssbo_5_1.data[_392], ssbo_5_1.data[_392 + 1u], ssbo_5_1.data[_392 + 2u]);
        uint _406 = (_390 * 34u) + 9u;
        uvec3 _415 = uvec3(ssbo_5_1.data[_406], ssbo_5_1.data[_406 + 1u], ssbo_5_1.data[_406 + 2u]);
        uint _420 = (_390 * 34u) + 12u;
        uvec3 _429 = uvec3(ssbo_5_1.data[_420], ssbo_5_1.data[_420 + 1u], ssbo_5_1.data[_420 + 2u]);
        uint _433 = _390 * 34u;
        uvec3 _442 = uvec3(ssbo_5_1.data[_433], ssbo_5_1.data[_433 + 1u], ssbo_5_1.data[_433 + 2u]);
        uint _447 = (_390 * 34u) + 15u;
        uvec3 _456 = uvec3(ssbo_5_1.data[_447], ssbo_5_1.data[_447 + 1u], ssbo_5_1.data[_447 + 2u]);
        uint _461 = (_390 * 34u) + 3u;
        uvec3 _470 = uvec3(ssbo_5_1.data[_461], ssbo_5_1.data[_461 + 1u], ssbo_5_1.data[_461 + 2u]);
        precise float _479 = (-2.0) * _181;
        precise float _481 = _479 + 1.0;
        precise float _483 = uintBitsToFloat(_401.x) + _374;
        precise float _485 = uintBitsToFloat(_401.y) + _378;
        precise float _487 = uintBitsToFloat(_401.z) + _382;
        precise float _489 = uintBitsToFloat(_415.x) + _362;
        precise float _491 = uintBitsToFloat(_415.y) + _366;
        precise float _493 = uintBitsToFloat(_415.z) + _370;
        precise float _495 = _180 * uintBitsToFloat(_429.x);
        precise float _496 = _495 + _483;
        precise float _498 = _180 * uintBitsToFloat(_429.y);
        precise float _499 = _498 + _485;
        precise float _501 = _180 * uintBitsToFloat(_429.z);
        precise float _502 = _501 + _487;
        precise float _504 = _180 * uintBitsToFloat(_442.x);
        precise float _505 = _504 + _489;
        precise float _507 = _180 * uintBitsToFloat(_442.y);
        precise float _508 = _507 + _491;
        precise float _510 = _180 * uintBitsToFloat(_442.z);
        precise float _511 = _510 + _493;
        precise float _513 = uintBitsToFloat(_456.x) * _481;
        precise float _514 = _513 + _496;
        precise float _516 = _514 * 0.5;
        precise float _519 = uintBitsToFloat(_456.y) * _481;
        precise float _520 = _519 + _499;
        precise float _521 = _520 * 0.5;
        precise float _524 = uintBitsToFloat(_456.z) * _481;
        precise float _525 = _524 + _502;
        precise float _526 = _525 * 0.5;
        precise float _529 = uintBitsToFloat(_470.x) * _481;
        precise float _530 = _529 + _505;
        precise float _531 = _530 * 0.5;
        precise float _534 = uintBitsToFloat(_470.y) * _481;
        precise float _535 = _534 + _508;
        precise float _536 = _535 * 0.5;
        precise float _539 = uintBitsToFloat(_470.z) * _481;
        precise float _540 = _539 + _511;
        precise float _541 = _540 * 0.5;
        precise float _545 = uintBitsToFloat(ssbo_5_1.data[_275]) + uintBitsToFloat(ssbo_5_1.data[(_390 * 34u) + 33u]);
        precise float _546 = _545 * 0.5;
        _548 = floatBitsToUint(_546);
        _549 = floatBitsToUint(_526);
        _550 = floatBitsToUint(_516);
        _551 = floatBitsToUint(_521);
        _552 = floatBitsToUint(_541);
        _553 = floatBitsToUint(_536);
        _554 = floatBitsToUint(_531);
    }
    else
    {
        _548 = ssbo_5_1.data[_275];
        _549 = floatBitsToUint(_382);
        _550 = floatBitsToUint(_374);
        _551 = floatBitsToUint(_378);
        _552 = floatBitsToUint(_370);
        _553 = floatBitsToUint(_366);
        _554 = floatBitsToUint(_362);
    }
    uint _580 = gl_SubgroupInvocationID & 63u;
    bool _586 = ((((_580 >= 32u) ? _386 : _385) >> (_580 & 31u)) & 1u) != 0u;
    precise float _605 = uintBitsToFloat(srt_flatbuf_1.data[63u]) * uintBitsToFloat(srt_flatbuf_1.data[37u]);
    precise float _608 = uintBitsToFloat(srt_flatbuf_1.data[35u]) * uintBitsToFloat(srt_flatbuf_1.data[64u]);
    precise float _612 = uintBitsToFloat(srt_flatbuf_1.data[36u]) * (-uintBitsToFloat(srt_flatbuf_1.data[64u]));
    precise float _613 = _612 + _605;
    precise float _616 = uintBitsToFloat(srt_flatbuf_1.data[62u]) * uintBitsToFloat(srt_flatbuf_1.data[36u]);
    precise float _619 = uintBitsToFloat(srt_flatbuf_1.data[62u]) * uintBitsToFloat(srt_flatbuf_1.data[38u]);
    precise float _620 = _619 + _613;
    precise float _624 = uintBitsToFloat(srt_flatbuf_1.data[37u]) * (-uintBitsToFloat(srt_flatbuf_1.data[62u]));
    precise float _625 = _624 + _608;
    precise float _628 = uintBitsToFloat(srt_flatbuf_1.data[63u]) * uintBitsToFloat(srt_flatbuf_1.data[38u]);
    precise float _629 = _628 + _625;
    precise float _632 = uintBitsToFloat(srt_flatbuf_1.data[62u]) * uintBitsToFloat(srt_flatbuf_1.data[35u]);
    precise float _635 = uintBitsToFloat(srt_flatbuf_1.data[35u]) * uintBitsToFloat(srt_flatbuf_1.data[65u]);
    precise float _636 = _635 + _620;
    precise float _641 = uintBitsToFloat(srt_flatbuf_1.data[35u]) * (-uintBitsToFloat(srt_flatbuf_1.data[63u]));
    precise float _642 = _641 + _616;
    precise float _643 = _636 * _636;
    precise float _646 = uintBitsToFloat(srt_flatbuf_1.data[64u]) * uintBitsToFloat(srt_flatbuf_1.data[38u]);
    precise float _647 = _646 + _642;
    precise float _650 = uintBitsToFloat(srt_flatbuf_1.data[65u]) * uintBitsToFloat(srt_flatbuf_1.data[36u]);
    precise float _651 = _650 + _629;
    precise float _655 = uintBitsToFloat(srt_flatbuf_1.data[63u]) * uintBitsToFloat(srt_flatbuf_1.data[36u]);
    precise float _656 = _655 + _632;
    precise float _657 = _651 * _651;
    precise float _658 = _657 + _643;
    precise float _661 = uintBitsToFloat(srt_flatbuf_1.data[65u]) * uintBitsToFloat(srt_flatbuf_1.data[37u]);
    precise float _662 = _661 + _647;
    precise float _666 = uintBitsToFloat(srt_flatbuf_1.data[64u]) * uintBitsToFloat(srt_flatbuf_1.data[37u]);
    precise float _667 = _666 + _656;
    precise float _669 = _662 * _662;
    precise float _670 = _669 + _658;
    precise float _674 = uintBitsToFloat(srt_flatbuf_1.data[65u]) * uintBitsToFloat(srt_flatbuf_1.data[38u]);
    precise float _675 = _674 + (-_667);
    precise float _677 = _675 * _675;
    precise float _678 = _677 + _670;
    bool _681 = _586 && isinf(_678);
    uvec4 _684 = subgroupBallot(_586 && (0.0 == _678));
    precise float _687 = (-1.0) + _678;
    uvec4 _693 = subgroupBallot(_586 && (abs(_687) <= 4.9999999873762135393917560577393e-07));
    uint _696 = uint(_681);
    uint _698 = gl_SubgroupInvocationID & 63u;
    uint _707 = gl_SubgroupInvocationID & 63u;
    uint _716 = gl_SubgroupInvocationID & 63u;
    bool _723 = (((((_716 >= 32u) ? _693.y : _693.x) >> (_716 & 31u)) & 1u) != 0u) || ((((((_707 >= 32u) ? _684.y : _684.x) >> (_707 & 31u)) & 1u) != 0u) || ((((((_698 >= 32u) ? _386 : _385) >> (_698 & 31u)) & 1u) != 0u) && _681));
    uint _746;
    uint _747;
    uint _748;
    uint _749;
    if (_723)
    {
        uvec4 _727 = subgroupBallot(_586 && (0.0 == _678));
        uint _733 = gl_SubgroupInvocationID & 63u;
        bool _740 = (((((_733 >= 32u) ? _727.y : _727.x) >> (_733 & 31u)) & 1u) != 0u) || (_586 && (0u != _696));
        _746 = _740 ? 1065353216u : floatBitsToUint(_675);
        _747 = _740 ? 0u : floatBitsToUint(_662);
        _748 = _740 ? 0u : floatBitsToUint(_651);
        _749 = _740 ? 0u : floatBitsToUint(_636);
    }
    else
    {
        _746 = _696;
        _747 = srt_flatbuf_1.data[36u];
        _748 = floatBitsToUint(_667);
        _749 = floatBitsToUint(_678);
    }
    uint _760;
    uint _761;
    uint _762;
    uint _763;
    if (!_723)
    {
        float _751 = inversesqrt(uintBitsToFloat(_749));
        precise float _752 = _751 * _636;
        precise float _754 = _751 * _651;
        precise float _756 = _751 * _662;
        precise float _758 = _751 * _675;
        _760 = floatBitsToUint(_758);
        _761 = floatBitsToUint(_756);
        _762 = floatBitsToUint(_754);
        _763 = floatBitsToUint(_752);
    }
    else
    {
        _760 = _746;
        _761 = _747;
        _762 = _748;
        _763 = _749;
    }
    precise float _802 = uintBitsToFloat(srt_flatbuf_1.data[71u]) * uintBitsToFloat(srt_flatbuf_1.data[45u]);
    precise float _805 = uintBitsToFloat(srt_flatbuf_1.data[43u]) * uintBitsToFloat(srt_flatbuf_1.data[72u]);
    precise float _809 = uintBitsToFloat(srt_flatbuf_1.data[44u]) * (-uintBitsToFloat(srt_flatbuf_1.data[72u]));
    precise float _810 = _809 + _802;
    precise float _813 = uintBitsToFloat(srt_flatbuf_1.data[70u]) * uintBitsToFloat(srt_flatbuf_1.data[44u]);
    precise float _816 = uintBitsToFloat(srt_flatbuf_1.data[70u]) * uintBitsToFloat(srt_flatbuf_1.data[46u]);
    precise float _817 = _816 + _810;
    precise float _821 = uintBitsToFloat(srt_flatbuf_1.data[45u]) * (-uintBitsToFloat(srt_flatbuf_1.data[70u]));
    precise float _822 = _821 + _805;
    precise float _825 = uintBitsToFloat(srt_flatbuf_1.data[71u]) * uintBitsToFloat(srt_flatbuf_1.data[46u]);
    precise float _826 = _825 + _822;
    precise float _829 = uintBitsToFloat(srt_flatbuf_1.data[70u]) * uintBitsToFloat(srt_flatbuf_1.data[43u]);
    precise float _832 = uintBitsToFloat(srt_flatbuf_1.data[43u]) * uintBitsToFloat(srt_flatbuf_1.data[73u]);
    precise float _833 = _832 + _817;
    uint _834 = floatBitsToUint(_833);
    precise float _838 = uintBitsToFloat(srt_flatbuf_1.data[43u]) * (-uintBitsToFloat(srt_flatbuf_1.data[71u]));
    precise float _839 = _838 + _813;
    precise float _841 = _833 * _833;
    precise float _844 = uintBitsToFloat(srt_flatbuf_1.data[72u]) * uintBitsToFloat(srt_flatbuf_1.data[46u]);
    precise float _845 = _844 + _839;
    precise float _848 = uintBitsToFloat(srt_flatbuf_1.data[73u]) * uintBitsToFloat(srt_flatbuf_1.data[44u]);
    precise float _849 = _848 + _826;
    precise float _853 = uintBitsToFloat(srt_flatbuf_1.data[71u]) * uintBitsToFloat(srt_flatbuf_1.data[44u]);
    precise float _854 = _853 + _829;
    precise float _855 = _849 * _849;
    precise float _856 = _855 + _841;
    precise float _859 = uintBitsToFloat(srt_flatbuf_1.data[73u]) * uintBitsToFloat(srt_flatbuf_1.data[45u]);
    precise float _860 = _859 + _845;
    precise float _864 = uintBitsToFloat(srt_flatbuf_1.data[72u]) * uintBitsToFloat(srt_flatbuf_1.data[45u]);
    precise float _865 = _864 + _854;
    precise float _869 = uintBitsToFloat(srt_flatbuf_1.data[73u]) * uintBitsToFloat(srt_flatbuf_1.data[46u]);
    precise float _870 = _869 + (-_865);
    precise float _872 = _860 * _860;
    precise float _873 = _872 + _856;
    precise float _874 = _870 * _870;
    precise float _875 = _874 + _873;
    bool _877 = _586 && isinf(_875);
    uvec4 _880 = subgroupBallot(_586 && (0.0 == _875));
    precise float _883 = (-1.0) + _875;
    uvec4 _887 = subgroupBallot(_586 && (abs(_883) <= 4.9999999873762135393917560577393e-07));
    uint _890 = uint(_877);
    uint _893 = gl_SubgroupInvocationID & 63u;
    uint _902 = gl_SubgroupInvocationID & 63u;
    bool _909 = (((((_902 >= 32u) ? _887.y : _887.x) >> (_902 & 31u)) & 1u) != 0u) || ((((((_893 >= 32u) ? _880.y : _880.x) >> (_893 & 31u)) & 1u) != 0u) || (_586 && _877));
    uint _931;
    uint _932;
    uint _933;
    uint _934;
    if (_909)
    {
        uvec4 _913 = subgroupBallot(_586 && (0.0 == _875));
        uint _919 = gl_SubgroupInvocationID & 63u;
        bool _926 = (((((_919 >= 32u) ? _913.y : _913.x) >> (_919 & 31u)) & 1u) != 0u) || (_586 && (0u != _890));
        _931 = _926 ? 1065353216u : floatBitsToUint(_870);
        _932 = _926 ? 0u : floatBitsToUint(_849);
        _933 = _926 ? 0u : _834;
        _934 = _926 ? 0u : floatBitsToUint(_860);
    }
    else
    {
        _931 = floatBitsToUint(_839);
        _932 = _890;
        _933 = srt_flatbuf_1.data[46u];
        _934 = _834;
    }
    uint _945;
    uint _946;
    uint _947;
    uint _948;
    if (!_909)
    {
        float _935 = inversesqrt(_875);
        precise float _937 = _935 * uintBitsToFloat(_934);
        precise float _939 = _935 * _849;
        precise float _941 = _935 * _860;
        precise float _943 = _935 * _870;
        _945 = floatBitsToUint(_943);
        _946 = floatBitsToUint(_939);
        _947 = floatBitsToUint(_937);
        _948 = floatBitsToUint(_941);
    }
    else
    {
        _945 = _931;
        _946 = _932;
        _947 = _933;
        _948 = _934;
    }
    bool _951 = ((push_data.ud_regs1.x >> 0u) & 1u) == 1u;
    uint _961;
    if (_951)
    {
        _961 = floatBitsToUint(-uintBitsToFloat(srt_flatbuf_1.data[56u]));
    }
    else
    {
        _961 = srt_flatbuf_1.data[45u];
    }
    uint _965;
    if (!_951)
    {
        _965 = srt_flatbuf_1.data[56u];
    }
    else
    {
        _965 = _961;
    }
    precise float _968 = uintBitsToFloat(_554) * uintBitsToFloat(_761);
    precise float _1030 = uintBitsToFloat(_552) * uintBitsToFloat(_762);
    precise float _1033 = uintBitsToFloat(_553) * uintBitsToFloat(_763);
    precise float _1036 = uintBitsToFloat(_550) * uintBitsToFloat(_948);
    precise float _1039 = uintBitsToFloat(_549) * uintBitsToFloat(_946);
    precise float _1043 = (-uintBitsToFloat(_763)) * uintBitsToFloat(_552);
    precise float _1044 = _1043 + _968;
    precise float _1048 = (-uintBitsToFloat(_761)) * uintBitsToFloat(_553);
    precise float _1049 = _1048 + _1030;
    precise float _1052 = uintBitsToFloat(_554) * uintBitsToFloat(_760);
    precise float _1053 = _1052 + _1049;
    precise float _1056 = uintBitsToFloat(_551) * uintBitsToFloat(_947);
    precise float _1059 = uintBitsToFloat(_760) * uintBitsToFloat(_553);
    precise float _1060 = _1059 + _1044;
    precise float _1064 = (-uintBitsToFloat(_762)) * uintBitsToFloat(_554);
    precise float _1065 = _1064 + _1033;
    precise float _1069 = (-uintBitsToFloat(_947)) * uintBitsToFloat(_549);
    precise float _1070 = _1069 + _1036;
    precise float _1074 = (-uintBitsToFloat(_948)) * uintBitsToFloat(_551);
    precise float _1075 = _1074 + _1039;
    precise float _1077 = uintBitsToFloat(_761) * _1060;
    precise float _1079 = uintBitsToFloat(_762) * _1053;
    precise float _1083 = uintBitsToFloat(_550) * (-uintBitsToFloat(_946));
    precise float _1084 = _1083 + _1056;
    precise float _1087 = uintBitsToFloat(_760) * uintBitsToFloat(_552);
    precise float _1088 = _1087 + _1065;
    precise float _1091 = uintBitsToFloat(_945) * uintBitsToFloat(_551);
    precise float _1092 = _1091 + _1070;
    precise float _1095 = uintBitsToFloat(_945) * uintBitsToFloat(_550);
    precise float _1096 = _1095 + _1075;
    precise float _1099 = (-_1088) * uintBitsToFloat(_762);
    precise float _1100 = _1099 + _1077;
    precise float _1103 = uintBitsToFloat(srt_flatbuf_1.data[31u]) * uintBitsToFloat(srt_flatbuf_1.data[64u]);
    precise float _1106 = uintBitsToFloat(srt_flatbuf_1.data[63u]) * uintBitsToFloat(srt_flatbuf_1.data[33u]);
    precise float _1110 = uintBitsToFloat(srt_flatbuf_1.data[33u]) * (-uintBitsToFloat(srt_flatbuf_1.data[62u]));
    precise float _1111 = _1110 + _1103;
    precise float _1114 = uintBitsToFloat(srt_flatbuf_1.data[62u]) * uintBitsToFloat(srt_flatbuf_1.data[32u]);
    precise float _1117 = uintBitsToFloat(srt_flatbuf_1.data[71u]) * uintBitsToFloat(srt_flatbuf_1.data[41u]);
    precise float _1121 = uintBitsToFloat(srt_flatbuf_1.data[32u]) * (-uintBitsToFloat(srt_flatbuf_1.data[64u]));
    precise float _1122 = _1121 + _1106;
    precise float _1125 = uintBitsToFloat(srt_flatbuf_1.data[39u]) * uintBitsToFloat(srt_flatbuf_1.data[72u]);
    precise float _1128 = uintBitsToFloat(srt_flatbuf_1.data[70u]) * uintBitsToFloat(srt_flatbuf_1.data[40u]);
    precise float _1131 = uintBitsToFloat(srt_flatbuf_1.data[32u]) * uintBitsToFloat(srt_flatbuf_1.data[65u]);
    precise float _1132 = _1131 + _1111;
    precise float _1136 = uintBitsToFloat(srt_flatbuf_1.data[31u]) * (-uintBitsToFloat(srt_flatbuf_1.data[63u]));
    precise float _1137 = _1136 + _1114;
    precise float _1140 = uintBitsToFloat(srt_flatbuf_1.data[31u]) * uintBitsToFloat(srt_flatbuf_1.data[65u]);
    precise float _1141 = _1140 + _1122;
    precise float _1145 = uintBitsToFloat(srt_flatbuf_1.data[41u]) * (-uintBitsToFloat(srt_flatbuf_1.data[70u]));
    precise float _1146 = _1145 + _1125;
    precise float _1150 = uintBitsToFloat(srt_flatbuf_1.data[40u]) * (-uintBitsToFloat(srt_flatbuf_1.data[72u]));
    precise float _1151 = _1150 + _1117;
    precise float _1153 = uintBitsToFloat(srt_flatbuf_1.data[64u]) * _1132;
    precise float _1156 = uintBitsToFloat(srt_flatbuf_1.data[33u]) * uintBitsToFloat(srt_flatbuf_1.data[65u]);
    precise float _1157 = _1156 + _1137;
    precise float _1159 = uintBitsToFloat(srt_flatbuf_1.data[63u]) * _1141;
    precise float _1162 = uintBitsToFloat(srt_flatbuf_1.data[40u]) * uintBitsToFloat(srt_flatbuf_1.data[73u]);
    precise float _1163 = _1162 + _1146;
    precise float _1167 = uintBitsToFloat(srt_flatbuf_1.data[39u]) * (-uintBitsToFloat(srt_flatbuf_1.data[71u]));
    precise float _1168 = _1167 + _1128;
    precise float _1171 = uintBitsToFloat(srt_flatbuf_1.data[39u]) * uintBitsToFloat(srt_flatbuf_1.data[73u]);
    precise float _1172 = _1171 + _1151;
    precise float _1174 = uintBitsToFloat(srt_flatbuf_1.data[72u]) * _1163;
    precise float _1176 = uintBitsToFloat(srt_flatbuf_1.data[71u]) * _1172;
    precise float _1178 = uintBitsToFloat(srt_flatbuf_1.data[62u]) * _1157;
    precise float _1181 = uintBitsToFloat(srt_flatbuf_1.data[63u]) * (-_1157);
    precise float _1182 = _1181 + _1153;
    precise float _1185 = uintBitsToFloat(srt_flatbuf_1.data[62u]) * (-_1132);
    precise float _1186 = _1185 + _1159;
    precise float _1189 = uintBitsToFloat(srt_flatbuf_1.data[41u]) * uintBitsToFloat(srt_flatbuf_1.data[73u]);
    precise float _1190 = _1189 + _1168;
    precise float _1192 = (-2.0) * _1182;
    precise float _1193 = _1192 + uintBitsToFloat(srt_flatbuf_1.data[31u]);
    precise float _1195 = (-2.0) * _1186;
    precise float _1196 = _1195 + uintBitsToFloat(srt_flatbuf_1.data[33u]);
    precise float _1198 = uintBitsToFloat(_948) * _1092;
    precise float _1200 = uintBitsToFloat(_946) * _1096;
    precise float _1203 = (-_1060) * uintBitsToFloat(_763);
    precise float _1204 = _1203 + _1079;
    precise float _1207 = uintBitsToFloat(srt_flatbuf_1.data[71u]) * (-_1190);
    precise float _1208 = _1207 + _1174;
    precise float _1211 = uintBitsToFloat(_945) * uintBitsToFloat(_549);
    precise float _1212 = _1211 + _1084;
    precise float _1215 = uintBitsToFloat(srt_flatbuf_1.data[70u]) * (-_1163);
    precise float _1216 = _1215 + _1176;
    precise float _1219 = uintBitsToFloat(srt_flatbuf_1.data[64u]) * (-_1141);
    precise float _1220 = _1219 + _1178;
    precise float _1222 = uintBitsToFloat(_763) * _1088;
    precise float _1224 = uintBitsToFloat(srt_flatbuf_1.data[70u]) * _1190;
    precise float _1226 = (-2.0) * _1100;
    precise float _1227 = _1226 + uintBitsToFloat(_554);
    precise float _1229 = (-2.0) * _1204;
    precise float _1230 = _1229 + uintBitsToFloat(_552);
    precise float _1232 = (-2.0) * _1208;
    precise float _1233 = _1232 + uintBitsToFloat(srt_flatbuf_1.data[39u]);
    precise float _1235 = (-2.0) * _1220;
    precise float _1236 = _1235 + uintBitsToFloat(srt_flatbuf_1.data[32u]);
    precise float _1239 = uintBitsToFloat(srt_flatbuf_1.data[61u]) * _1193;
    precise float _1240 = _1239 + uintBitsToFloat(srt_flatbuf_1.data[58u]);
    precise float _1243 = uintBitsToFloat(srt_flatbuf_1.data[34u]) * uintBitsToFloat(srt_flatbuf_1.data[61u]);
    precise float _1246 = uintBitsToFloat(srt_flatbuf_1.data[61u]) * _1196;
    precise float _1247 = _1246 + uintBitsToFloat(srt_flatbuf_1.data[60u]);
    precise float _1250 = (-_1212) * uintBitsToFloat(_946);
    precise float _1251 = _1250 + _1198;
    precise float _1253 = (-2.0) * _1216;
    precise float _1254 = _1253 + uintBitsToFloat(srt_flatbuf_1.data[41u]);
    precise float _1256 = uintBitsToFloat(_947) * _1212;
    precise float _1259 = (-_1092) * uintBitsToFloat(_947);
    precise float _1260 = _1259 + _1200;
    precise float _1263 = (-_1053) * uintBitsToFloat(_761);
    precise float _1264 = _1263 + _1222;
    precise float _1267 = uintBitsToFloat(srt_flatbuf_1.data[72u]) * (-_1172);
    precise float _1268 = _1267 + _1224;
    precise float _1269 = _1243 * _1227;
    precise float _1270 = _1269 + _1240;
    precise float _1271 = _1243 * _1230;
    precise float _1272 = _1271 + _1247;
    precise float _1275 = uintBitsToFloat(srt_flatbuf_1.data[42u]) * uintBitsToFloat(srt_flatbuf_1.data[69u]);
    precise float _1277 = (-2.0) * _1260;
    precise float _1278 = _1277 + uintBitsToFloat(_549);
    precise float _1281 = uintBitsToFloat(srt_flatbuf_1.data[61u]) * _1236;
    precise float _1282 = _1281 + uintBitsToFloat(srt_flatbuf_1.data[59u]);
    precise float _1284 = (-2.0) * _1264;
    precise float _1285 = _1284 + uintBitsToFloat(_553);
    precise float _1287 = (-2.0) * _1268;
    precise float _1288 = _1287 + uintBitsToFloat(srt_flatbuf_1.data[40u]);
    precise float _1291 = uintBitsToFloat(srt_flatbuf_1.data[69u]) * _1233;
    precise float _1292 = _1291 + uintBitsToFloat(srt_flatbuf_1.data[66u]);
    precise float _1294 = (-2.0) * _1251;
    precise float _1295 = _1294 + uintBitsToFloat(_550);
    precise float _1298 = uintBitsToFloat(srt_flatbuf_1.data[69u]) * _1254;
    precise float _1299 = _1298 + uintBitsToFloat(srt_flatbuf_1.data[68u]);
    precise float _1302 = (-_1096) * uintBitsToFloat(_948);
    precise float _1303 = _1302 + _1256;
    precise float _1305 = uintBitsToFloat(_965) + _1270;
    float _1306 = 1.0 / _1272;
    precise float _1307 = _1243 * _1285;
    precise float _1308 = _1307 + _1282;
    precise float _1309 = _1295 * _1275;
    precise float _1310 = _1309 + _1292;
    precise float _1311 = _1278 * _1275;
    precise float _1312 = _1311 + _1299;
    precise float _1315 = uintBitsToFloat(srt_flatbuf_1.data[69u]) * _1288;
    precise float _1316 = _1315 + uintBitsToFloat(srt_flatbuf_1.data[67u]);
    precise float _1318 = (-2.0) * _1303;
    precise float _1319 = _1318 + uintBitsToFloat(_551);
    precise float _1320 = _1306 * _1305;
    precise float _1322 = uintBitsToFloat(_965) + _1310;
    float _1323 = 1.0 / _1312;
    precise float _1324 = _1306 * _1308;
    precise float _1326 = _1319 * _1275;
    precise float _1327 = _1326 + _1316;
    precise float _1329 = _1323 * _1322;
    precise float _1330 = _1329 + (-_1320);
    precise float _1333 = _1323 * _1327;
    precise float _1334 = _1333 + (-_1324);
    precise float _1336 = _1323 * _1322;
    precise float _1337 = _1323 * _1327;
    uint _1391;
    uint _1392;
    if (0u != srt_flatbuf_1.data[57u])
    {
        precise float _1373 = uintBitsToFloat(srt_flatbuf_1.data[47u]) * _1320;
        precise float _1374 = _1373 + uintBitsToFloat(srt_flatbuf_1.data[49u]);
        precise float _1377 = uintBitsToFloat(srt_flatbuf_1.data[48u]) * _1324;
        precise float _1378 = _1377 + uintBitsToFloat(srt_flatbuf_1.data[50u]);
        precise float _1380 = uintBitsToFloat(srt_flatbuf_1.data[53u]) - _1374;
        precise float _1382 = uintBitsToFloat(srt_flatbuf_1.data[54u]) - _1378;
        precise float _1384 = uintBitsToFloat(srt_flatbuf_1.data[51u]) * _1336;
        precise float _1385 = _1384 + _1380;
        precise float _1388 = uintBitsToFloat(srt_flatbuf_1.data[52u]) * _1337;
        precise float _1389 = _1388 + _1382;
        _1391 = floatBitsToUint(_1389);
        _1392 = floatBitsToUint(_1385);
    }
    else
    {
        _1391 = floatBitsToUint(_1334);
        _1392 = floatBitsToUint(_1330);
    }
    uint _1394 = (_184 * 34u) + 31u;
    uint _1396 = ssbo_5_1.data[_1394];
    uint _1399 = ssbo_5_1.data[_1394 + 1u];
    uvec2 _1400 = uvec2(_1396, _1399);
    uint _1401 = _1400.x;
    uint _1402 = _1400.y;
    uint _1405 = (_184 * 34u) + 27u;
    uint _1407 = ssbo_5_1.data[_1405];
    uint _1410 = ssbo_5_1.data[_1405 + 1u];
    uint _1413 = ssbo_5_1.data[_1405 + 2u];
    uvec3 _1414 = uvec3(_1407, _1410, _1413);
    uint _1421 = srt_flatbuf_1.data[30u];
    precise float _1425 = (-uintBitsToFloat(_965)) + (-_1240);
    precise float _1428 = (-uintBitsToFloat(_761)) * _1425;
    precise float _1431 = _1247 * (-uintBitsToFloat(_763));
    precise float _1432 = _1431 + _1428;
    precise float _1435 = uintBitsToFloat(_760) * (-_1282);
    precise float _1436 = _1435 + _1432;
    uvec4 _1439 = subgroupBallot(_586 && (2u <= uint(gl_VertexIndex)));
    uint _1443 = _184 + 12345u;
    precise float _1446 = uintBitsToFloat(_762) * _1247;
    precise float _1449 = uintBitsToFloat(_763) * _1282;
    precise float _1451 = _1425 * uintBitsToFloat(_762);
    precise float _1452 = _1451 + _1449;
    uint _1454 = push_data.ud_regs1.x << 6u;
    precise float _1457 = uintBitsToFloat(_760) * (-_1247);
    precise float _1458 = _1457 + _1452;
    precise float _1462 = _1282 * (-uintBitsToFloat(_761));
    precise float _1463 = _1462 + _1446;
    precise float _1465 = uintBitsToFloat(_760) * _1425;
    precise float _1466 = _1465 + _1463;
    precise float _1469 = (-uintBitsToFloat(_761)) * _1436;
    precise float _1471 = _1458 * uintBitsToFloat(_762);
    precise float _1472 = _1471 + _1469;
    uint _1473 = ((61u ^ (_1443 >> 16u)) ^ _1443) * 9u;
    uint _1480 = (_1454 + 388u) >> 2u;
    uvec2 _1481 = uvec2(push_data.ud_regs0.z, push_data.ud_regs0.w);
    uint _1482 = read_const_dynamic(_1481, _1480);
    uint _1484 = read_const_dynamic(_1481, _1480 + 1u);
    uint _1486 = read_const_dynamic(_1481, _1480 + 2u);
    uint _1488 = read_const_dynamic(_1481, _1480 + 3u);
    uint _1489 = (_1454 + 340u) >> 2u;
    uvec2 _1490 = uvec2(push_data.ud_regs0.z, push_data.ud_regs0.w);
    uint _1491 = read_const_dynamic(_1490, _1489);
    uint _1493 = read_const_dynamic(_1490, _1489 + 1u);
    uint _1495 = read_const_dynamic(_1490, _1489 + 2u);
    uint _1497 = read_const_dynamic(_1490, _1489 + 3u);
    uint _1500 = (_1454 + 356u) >> 2u;
    uvec2 _1501 = uvec2(push_data.ud_regs0.z, push_data.ud_regs0.w);
    uint _1502 = read_const_dynamic(_1501, _1500);
    uint _1504 = read_const_dynamic(_1501, _1500 + 1u);
    uint _1506 = read_const_dynamic(_1501, _1500 + 2u);
    uint _1508 = read_const_dynamic(_1501, _1500 + 3u);
    uint _1513 = (_1454 + 372u) >> 2u;
    uvec2 _1514 = uvec2(push_data.ud_regs0.z, push_data.ud_regs0.w);
    uint _1515 = read_const_dynamic(_1514, _1513);
    uint _1517 = read_const_dynamic(_1514, _1513 + 1u);
    uint _1519 = read_const_dynamic(_1514, _1513 + 2u);
    uint _1521 = read_const_dynamic(_1514, _1513 + 3u);
    precise float _1529 = (-uintBitsToFloat(_763)) * _1458;
    precise float _1531 = _1466 * uintBitsToFloat(_761);
    precise float _1532 = _1531 + _1529;
    precise float _1535 = (-uintBitsToFloat(_762)) * _1466;
    precise float _1537 = _1436 * uintBitsToFloat(_763);
    precise float _1538 = _1537 + _1535;
    uint _1540 = ((_1473 >> 4u) ^ _1473) * 668265261u;
    float _1541 = 1.0 / _1243;
    precise float _1543 = (-2.0) * _1532;
    precise float _1544 = _1543 + (-_1282);
    precise float _1546 = (-2.0) * _1538;
    precise float _1547 = _1546 + (-_1247);
    precise float _1549 = (-2.0) * _1472;
    precise float _1550 = _1549 + _1425;
    uint _1552 = gl_SubgroupInvocationID & 63u;
    full_result_u32x2 _1560;
    _1560._m0 = uaddCarry(0u, _1421 * 200u, _1560._m1);
    full_result_u32x2 _1562;
    _1562._m0 = uaddCarry(_1560._m0, uint(((((_1552 >= 32u) ? _1439.y : _1439.x) >> (_1552 & 31u)) & 1u) != 0u), _1562._m1);
    precise float _1564 = _1541 * _1550;
    precise float _1565 = _1541 * _1544;
    precise float _1569 = uintBitsToFloat(_1491) * _1305;
    precise float _1570 = _1569 + uintBitsToFloat(_1482);
    precise float _1573 = _1305 * uintBitsToFloat(_1497);
    precise float _1574 = _1573 + uintBitsToFloat(_1488);
    precise float _1577 = _1305 * uintBitsToFloat(_1495);
    precise float _1578 = _1577 + uintBitsToFloat(_1486);
    precise float _1581 = uintBitsToFloat(_1493) * _1305;
    precise float _1582 = _1581 + uintBitsToFloat(_1484);
    precise float _1584 = uintBitsToFloat(_1502) * _1308;
    precise float _1585 = _1584 + _1570;
    precise float _1587 = uintBitsToFloat(_1508) * _1308;
    precise float _1588 = _1587 + _1574;
    precise float _1590 = uintBitsToFloat(_1506) * _1308;
    precise float _1591 = _1590 + _1578;
    precise float _1593 = uintBitsToFloat(_1504) * _1308;
    precise float _1594 = _1593 + _1582;
    precise float _1596 = uintBitsToFloat(_1515) * _1272;
    precise float _1597 = _1596 + _1585;
    precise float _1599 = _1272 * uintBitsToFloat(_1521);
    precise float _1600 = _1599 + _1588;
    precise float _1602 = uintBitsToFloat(_1519) * _1272;
    precise float _1603 = _1602 + _1591;
    precise float _1605 = uintBitsToFloat(_1517) * _1272;
    precise float _1606 = _1605 + _1594;
    gl_Layer = int(floatBitsToUint(uintBitsToFloat(push_data.ud_regs1.x)));
    gl_Position.x = _1597;
    gl_Position.y = _1606;
    gl_Position.z = _1603;
    gl_Position.w = _1600;
    precise float _1613 = _1541 * _1547;
    precise float _1614 = 1.0 - _181;
    precise float _1617 = uintBitsToFloat(srt_flatbuf_1.data[55u]) * uintBitsToFloat(_1392);
    precise float _1620 = uintBitsToFloat(srt_flatbuf_1.data[55u]) * uintBitsToFloat(_1391);
    precise float _1632 = 0.0039215688593685626983642578125 * float(bitfieldExtract(_1401, int(0u), int(8u)));
    out_attr6.x = _1564;
    out_attr6.y = _1565;
    out_attr6.z = _1613;
    out_attr6.w = 0.0;
    out_attr5.x = uintBitsToFloat((_1540 >> 15u) ^ _1540);
    out_attr5.y = uintBitsToFloat(_1401);
    out_attr5.z = uintBitsToFloat(_1402);
    out_attr5.w = 0.0;
    out_attr4.x = uintBitsToFloat(_1414.x);
    out_attr4.y = uintBitsToFloat(_1414.y);
    out_attr4.z = uintBitsToFloat(_1414.z);
    out_attr4.w = _1632;
    out_attr3.x = _175;
    out_attr3.y = _1614;
    out_attr3.z = float(bitfieldExtract(_1402, int(24u), int(8u)));
    out_attr3.w = 0.0;
    out_attr2.x = uintBitsToFloat(ssbo_6_1.data[((_1562._m0 + (255u & _1402)) * 4u) + 3u]);
    out_attr2.y = 0.0;
    out_attr2.z = 0.0;
    out_attr2.w = uintBitsToFloat(_548);
    out_attr1.x = uintBitsToFloat(_554);
    out_attr1.y = uintBitsToFloat(_553);
    out_attr1.z = uintBitsToFloat(_552);
    out_attr1.w = 0.0;
    out_attr0.x = _1617;
    out_attr0.y = _1620;
    out_attr0.z = 0.0;
    out_attr0.w = 0.0;
}

