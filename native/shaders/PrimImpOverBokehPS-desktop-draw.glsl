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
#extension GL_AMD_shader_explicit_vertex_parameter : require
#extension GL_KHR_shader_subgroup_ballot : require
#extension GL_KHR_shader_subgroup_basic : require
#extension GL_EXT_samplerless_texture_functions : require
#extension GL_AMD_shader_trinary_minmax : require
#extension GL_EXT_demote_to_helper_invocation : require

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

layout(set = 0, binding = 0, std430) readonly buffer ssbo_1
{
    uint data[];
} ssbo_1_1;

layout(set = 0, binding = 1, std430) readonly buffer ssbo_2
{
    uint data[];
} ssbo_2_1;

layout(set = 0, binding = 2, std430) readonly buffer ssbo_3
{
    uint data[];
} ssbo_3_1;

layout(set = 0, binding = 3, std430) readonly buffer srt_flatbuf
{
    uint data[];
} srt_flatbuf_1;

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

layout(set = 0, binding = 4) uniform texture2D fs_img40;
layout(set = 0, binding = 5) uniform texture2D fs_img16;
layout(set = 0, binding = 6) uniform texture2D fs_img24;
layout(set = 0, binding = 7) uniform texture2DArray fs_img32;
layout(set = 0, binding = 8) uniform sampler fs_sampsgpr_91;
layout(set = 0, binding = 9) uniform sampler fs_sampsgpr_95;

layout(location = 0) in vec4 fs_in_attr0;
layout(location = 1) in vec4 fs_in_attr1;
layout(location = 2) in vec4 fs_in_attr2;
layout(location = 3) in vec4 fs_in_attr3;
layout(location = 4) in vec4 fs_in_attr4;
layout(location = 5) __explicitInterpAMD in vec4 fs_in_attr5;
layout(location = 6) in vec4 fs_in_attr6;
layout(location = 0) out uvec4 frag_color0;

void main()
{
    vec4 _131 = interpolateAtVertexAMD(fs_in_attr5, 0u);
    uvec4 _148 = subgroupBallot(true);
    uvec4 _151 = subgroupBallot(true);
    uint64_t _155 = packUint2x32(uvec2(_151.xy));
    uint64_t _163 = (((_155 | (_155 >> 1u)) | (_155 >> 2u)) | (_155 >> 3u)) & 1229782938247303441ul;
    bool _175 = (((((_163 | (_163 << 1u)) | (_163 << 2u)) | (_163 << 3u)) >> (gl_SubgroupInvocationID & 63u)) & 1ul) != 0ul;
    vec4 _190 = texture(sampler2DArray(fs_img32, fs_sampsgpr_95), vec3(fs_in_attr3.x, fs_in_attr3.y, roundEven(fs_in_attr3.z)));
    uint _192 = floatBitsToUint(_190.x);
    uint _194 = floatBitsToUint(_131.x);
    uvec4 _202 = subgroupBallot(_175 && (200.0 <= fs_in_attr3.z));
    uvec4 _216 = subgroupBallot(_175 && (220.0 <= fs_in_attr3.z));
    uint _220 = gl_SubgroupInvocationID & 63u;
    uvec4 _229 = subgroupBallot(_175);
    bool _232 = _175 && (((((_220 >= 32u) ? _202.y : _202.x) >> (_220 & 31u)) & 1u) != 0u);
    uint _367;
    uint _368;
    if (_232)
    {
        uvec4 _233 = subgroupBallot(_232);
        bool _236 = _232 && (_175 && (221.0 <= fs_in_attr3.z));
        uint _266;
        uint _267;
        uint _268;
        uint _269;
        if (_236)
        {
            precise float _238 = (-0.5) + fs_in_attr3.x;
            bool _242 = _236 && (abs(_238) <= 0.5);
            precise float _247 = 2.0 * abs(_238);
            float _249 = clamp(_247, 0.0, 1.0);
            precise float _252 = uintBitsToFloat(_242 ? 3212836864u : 0u) - _249;
            precise float _253 = 1.0 + _252;
            precise float _258 = 0.100000001490116119384765625 * fs_in_attr3.z;
            precise float _260 = _258 + (-22.1000003814697265625);
            precise float _263 = _253 * clamp(_260, 0.0, 1.0);
            precise float _264 = _263 + uintBitsToFloat(_242 ? 1065353216u : 0u);
            _266 = 1u;
            _267 = floatBitsToUint(_264);
            _268 = floatBitsToUint(_249);
            _269 = floatBitsToUint(_253);
        }
        else
        {
            _266 = 0u;
            _267 = _192;
            _268 = floatBitsToUint(fs_in_attr3.y);
            _269 = floatBitsToUint(fs_in_attr3.x);
        }
        uint _271 = gl_SubgroupInvocationID & 63u;
        bool _279 = (((((_271 >= 32u) ? _233.y : _233.x) >> (_271 & 31u)) & 1u) != 0u) && (!_236);
        uint _365;
        uint _366;
        if (_279)
        {
            uint _281 = gl_SubgroupInvocationID & 63u;
            uvec4 _288 = subgroupBallot(_279);
            bool _291 = _279 && (((((_281 >= 32u) ? _216.y : _216.x) >> (_281 & 31u)) & 1u) != 0u);
            uint _325;
            uint _326;
            uint _327;
            uint _328;
            if (_291)
            {
                precise float _300 = (-0.5) + uintBitsToFloat(_269);
                precise float _308 = _300 * _300;
                precise float _311 = fs_in_attr2.x * (1.0 / uintBitsToFloat(ssbo_2_1.data[((srt_flatbuf_1.data[64u] * 208u) + 172u) >> 2u]));
                precise float _313 = 0.5 * clamp(_311, 0.0, 1.0);
                precise float _314 = _313 + (-0.5);
                precise float _316 = _314 * _314;
                precise float _317 = _316 + _308;
                float _318 = sqrt(_317);
                precise float _321 = (-2.0) * _318;
                precise float _322 = _321 + 1.0;
                _325 = 1u;
                _326 = floatBitsToUint(clamp(_322, 0.0, 1.0));
                _327 = floatBitsToUint(_314);
                _328 = floatBitsToUint(_318);
            }
            else
            {
                _325 = _266;
                _326 = _267;
                _327 = _268;
                _328 = _269;
            }
            uint _330 = gl_SubgroupInvocationID & 63u;
            bool _338 = (((((_330 >= 32u) ? _288.y : _288.x) >> (_330 & 31u)) & 1u) != 0u) && (!_291);
            uint _364;
            if (_338)
            {
                precise float _340 = (-0.5) + uintBitsToFloat(_328);
                precise float _341 = _340 * _340;
                precise float _343 = (-0.5) + uintBitsToFloat(_327);
                precise float _344 = _343 * _343;
                precise float _345 = _344 + _341;
                float _346 = sqrt(_345);
                bool _348 = _338 && (0.5 >= _346);
                precise float _350 = 2.0 * _346;
                precise float _353 = uintBitsToFloat(_348 ? 3212836864u : 0u) - clamp(_350, 0.0, 1.0);
                precise float _354 = 1.0 + _353;
                precise float _356 = 0.100000001490116119384765625 * fs_in_attr3.z;
                precise float _358 = _356 + (-20.0);
                precise float _361 = _354 * clamp(_358, 0.0, 1.0);
                precise float _362 = _361 + uintBitsToFloat(_348 ? 1065353216u : 0u);
                _364 = floatBitsToUint(_362);
            }
            else
            {
                _364 = _326;
            }
            _365 = _325;
            _366 = _364;
        }
        else
        {
            _365 = _266;
            _366 = _267;
        }
        _367 = _365;
        _368 = _366;
    }
    else
    {
        _367 = 0u;
        _368 = _192;
    }
    uint _380 = gl_SubgroupInvocationID & 63u;
    bool _386 = ((((_380 >= 32u) ? _229.y : _229.x) >> (_380 & 31u)) & 1u) != 0u;
    precise float _389 = uintBitsToFloat(srt_flatbuf_1.data[78u]) * uintBitsToFloat(_368);
    precise float _395 = _389 * fs_in_attr4.w;
    uint _585;
    if (_386 && (uintBitsToFloat(srt_flatbuf_1.data[77u]) > 0.0))
    {
        precise float _397 = 0.5 * gl_FragCoord.z;
        precise float _417 = uintBitsToFloat(srt_flatbuf_1.data[73u]) * gl_FragCoord.x;
        precise float _418 = _417 + 0.5;
        precise float _420 = gl_FragCoord.y * uintBitsToFloat(srt_flatbuf_1.data[74u]);
        precise float _421 = _420 + 0.5;
        precise float _423 = uintBitsToFloat(srt_flatbuf_1.data[75u]) * gl_FragCoord.x;
        precise float _424 = _423 + 0.5;
        precise float _426 = gl_FragCoord.y * uintBitsToFloat(srt_flatbuf_1.data[76u]);
        precise float _427 = _426 + 0.5;
        uvec4 _434 = uvec4(uvec2(textureSize(fs_img16, int(0u))), 0u, 0u);
        precise float _437 = floor(_421) / float(_434.y);
        precise float _440 = floor(_418) / float(_434.x);
        vec4 _445 = textureGather(sampler2D(fs_img16, fs_sampsgpr_91), vec2(_440, _437));
        uvec4 _452 = uvec4(uvec2(textureSize(fs_img24, int(0u))), 0u, 0u);
        precise float _455 = floor(_427) / float(_452.y);
        precise float _458 = floor(_424) / float(_452.x);
        vec4 _463 = textureGather(sampler2D(fs_img24, fs_sampsgpr_91), vec2(_458, _455));
        float _469 = clamp(fract(_418), 0.0, 1.0);
        float _471 = clamp(fract(_424), 0.0, 1.0);
        precise float _472 = 1.0 - _469;
        float _474 = clamp(fract(_421), 0.0, 1.0);
        precise float _475 = 1.0 - _471;
        float _477 = clamp(fract(_427), 0.0, 1.0);
        precise float _478 = _474 * _472;
        precise float _480 = _477 * _475;
        precise float _482 = 1.0 - _474;
        precise float _483 = 1.0 - _477;
        uvec4 _488 = subgroupBallot(_386 && (_397 > _463.x));
        uint _491 = (_386 && (gl_FragCoord.z > _445.x)) ? floatBitsToUint(_478) : 0u;
        uint _493 = gl_SubgroupInvocationID & 63u;
        uint _500 = (((((_493 >= 32u) ? _488.y : _488.x) >> (_493 & 31u)) & 1u) != 0u) ? floatBitsToUint(_480) : 0u;
        precise float _502 = _469 * _474;
        precise float _503 = _502 + uintBitsToFloat(_491);
        uvec4 _507 = subgroupBallot(_386 && (gl_FragCoord.z > _445.y));
        precise float _511 = _471 * _477;
        precise float _512 = _511 + uintBitsToFloat(_500);
        uint _517 = gl_SubgroupInvocationID & 63u;
        uint _524 = (((((_517 >= 32u) ? _507.y : _507.x) >> (_517 & 31u)) & 1u) != 0u) ? floatBitsToUint(_503) : _491;
        uint _525 = (_386 && (_397 > _463.y)) ? floatBitsToUint(_512) : _500;
        precise float _527 = _469 * _482;
        precise float _528 = _527 + uintBitsToFloat(_524);
        uvec4 _532 = subgroupBallot(_386 && (gl_FragCoord.z > _445.z));
        precise float _536 = _471 * _483;
        precise float _537 = _536 + uintBitsToFloat(_525);
        uint _542 = gl_SubgroupInvocationID & 63u;
        uint _549 = (((((_542 >= 32u) ? _532.y : _532.x) >> (_542 & 31u)) & 1u) != 0u) ? floatBitsToUint(_528) : _524;
        uint _550 = (_386 && (_397 > _463.z)) ? floatBitsToUint(_537) : _525;
        precise float _552 = _472 * _482;
        precise float _553 = _552 + uintBitsToFloat(_549);
        uvec4 _557 = subgroupBallot(_386 && (gl_FragCoord.z > _445.w));
        precise float _561 = _475 * _483;
        precise float _562 = _561 + uintBitsToFloat(_550);
        uint _567 = gl_SubgroupInvocationID & 63u;
        precise float _580 = (-1.0) + min(uintBitsToFloat((((((_567 >= 32u) ? _557.y : _557.x) >> (_567 & 31u)) & 1u) != 0u) ? floatBitsToUint(_553) : _549), uintBitsToFloat((_386 && (_397 > _463.w)) ? floatBitsToUint(_562) : _550));
        precise float _582 = uintBitsToFloat(srt_flatbuf_1.data[77u]) * _580;
        precise float _583 = _582 + 1.0;
        _585 = floatBitsToUint(_583);
    }
    else
    {
        _585 = 1065353216u;
    }
    uint _590 = (srt_flatbuf_1.data[64u] * 208u) >> 2u;
    precise float _600 = gl_FragCoord.x - uintBitsToFloat(ssbo_2_1.data[_590]);
    precise float _601 = _600 * _600;
    precise float _603 = gl_FragCoord.y - uintBitsToFloat(ssbo_2_1.data[_590 + 1u]);
    precise float _604 = _603 * _603;
    precise float _605 = _604 + _601;
    uint _610 = gl_SubgroupInvocationID & 63u;
    bool _618 = (((((_610 >= 32u) ? _148.y : _148.x) >> (_610 & 31u)) & 1u) != 0u) && (!(_386 && (uintBitsToFloat(ssbo_2_1.data[_590 + 3u]) < _605)));
    uvec4 _619 = subgroupBallot(_618);
    uint _620 = _619.x;
    if (_618)
    {
        uint64_t _623 = packUint2x32(uvec2(_620, _619.y));
        uint64_t _630 = (((_623 | (_623 >> 1u)) | (_623 >> 2u)) | (_623 >> 3u)) & 1229782938247303441ul;
        bool _641 = (((((_630 | (_630 << 1u)) | (_630 << 2u)) | (_630 << 3u)) >> (gl_SubgroupInvocationID & 63u)) & 1ul) != 0ul;
        uint _643 = floatBitsToUint(_131.y);
        uint _645 = _643 >> 24u;
        uvec4 _648 = subgroupBallot(_641 && (1u < _645));
        uint _655 = gl_SubgroupInvocationID & 63u;
        uvec4 _663 = subgroupBallot(_641);
        uint _675;
        if (_641 && ((_641 && (1.0 == uintBitsToFloat(_585))) && (((((_655 >= 32u) ? _648.y : _648.x) >> (_655 & 31u)) & 1u) != 0u)))
        {
            precise float _670 = float(_645 + 4294967295u) * _395;
            precise float _672 = (-0.00393700785934925079345703125) * _670;
            precise float _673 = _672 + _395;
            _675 = floatBitsToUint(_673);
        }
        else
        {
            _675 = floatBitsToUint(_395);
        }
        uint _677 = gl_SubgroupInvocationID & 63u;
        bool _683 = ((((_677 >= 32u) ? _663.y : _663.x) >> (_677 & 31u)) & 1u) != 0u;
        uvec4 _687 = subgroupBallot(_683 && (0.0 == uintBitsToFloat(_675)));
        uint _698 = gl_SubgroupInvocationID & 63u;
        uint _707 = gl_SubgroupInvocationID & 63u;
        bool _715 = (((((_707 >= 32u) ? _619.y : _620) >> (_707 & 31u)) & 1u) != 0u) && (!((_683 && (uintBitsToFloat(_675) < texelFetch(fs_img40, ivec2(uvec2(127u & (uint(gl_FragCoord.x) + _194), 127u & ((_194 >> 16u) + uint(gl_FragCoord.y)))), 0).x)) || (((((_698 >= 32u) ? _687.y : _687.x) >> (_698 & 31u)) & 1u) != 0u)));
        uvec4 _716 = subgroupBallot(_715);
        uint _717 = _716.x;
        if (_715)
        {
            uint _719 = srt_flatbuf_1.data[64u] * 208u;
            uint64_t _721 = packUint2x32(uvec2(_717, _716.y));
            uint64_t _728 = (((_721 | (_721 >> 1u)) | (_721 >> 2u)) | (_721 >> 3u)) & 1229782938247303441ul;
            bool _739 = (((((_728 | (_728 << 1u)) | (_728 << 2u)) | (_728 << 3u)) >> (gl_SubgroupInvocationID & 63u)) & 1ul) != 0ul;
            uint _741 = (_719 + 32u) >> 2u;
            uint _747 = _741 + 2u;
            float _755 = float(bitfieldExtract(_643, int(8u), int(8u)));
            precise float _757 = 0.0039215688593685626983642578125 * _755;
            precise float _759 = (-0.0039215688593685626983642578125) * _755;
            precise float _761 = uintBitsToFloat(ssbo_2_1.data[_741]) * _757;
            precise float _762 = _761 + _759;
            precise float _765 = uintBitsToFloat(ssbo_2_1.data[_747]) * (-_757);
            precise float _766 = _765 + _759;
            precise float _767 = 1.0 + _762;
            precise float _769 = uintBitsToFloat(ssbo_2_1.data[_741 + 3u]) * _757;
            precise float _770 = _769 + _766;
            precise float _771 = 1.0 + _770;
            precise float _777 = (-0.0039215688593685626983642578125) * _755;
            precise float _778 = _777 + (-_767);
            uint _780 = (_719 + 156u) >> 2u;
            precise float _784 = uintBitsToFloat(ssbo_2_1.data[_741 + 1u]) * _757;
            precise float _785 = _784 + _778;
            precise float _788 = uintBitsToFloat(ssbo_2_1.data[_747]) * (-_757);
            precise float _789 = _788 + fs_in_attr2.w;
            precise float _790 = 1.0 + _785;
            precise float _791 = (1.0 / _771) * _789;
            precise float _798 = _790 * clamp(_791, 0.0, 1.0);
            precise float _799 = _798 + _767;
            precise float _804 = fs_in_attr4.x * _799;
            precise float _806 = fs_in_attr4.y * _799;
            precise float _808 = fs_in_attr4.z * _799;
            float _817 = float(bitfieldExtract(_643, int(16u), int(8u)));
            uint _1490;
            uint _1491;
            uint _1492;
            bool _1493;
            if (_739 && (uintBitsToFloat(ssbo_2_1.data[_780]) > 0.0))
            {
                uint _834 = srt_flatbuf_1.data[64u] * 208u;
                precise float _837 = uintBitsToFloat(srt_flatbuf_1.data[71u]) * fs_in_attr1.x;
                precise float _839 = uintBitsToFloat(srt_flatbuf_1.data[69u]) * fs_in_attr1.y;
                precise float _842 = (-uintBitsToFloat(srt_flatbuf_1.data[69u])) * fs_in_attr1.z;
                precise float _843 = _842 + _837;
                precise float _845 = uintBitsToFloat(srt_flatbuf_1.data[70u]) * fs_in_attr1.z;
                precise float _847 = uintBitsToFloat(srt_flatbuf_1.data[72u]) * fs_in_attr1.y;
                precise float _848 = _847 + _843;
                precise float _851 = (-uintBitsToFloat(srt_flatbuf_1.data[70u])) * fs_in_attr1.x;
                precise float _852 = _851 + _839;
                precise float _854 = uintBitsToFloat(srt_flatbuf_1.data[71u]) * _848;
                precise float _856 = uintBitsToFloat(srt_flatbuf_1.data[72u]) * fs_in_attr1.z;
                precise float _857 = _856 + _852;
                precise float _860 = (-uintBitsToFloat(srt_flatbuf_1.data[71u])) * fs_in_attr1.y;
                precise float _861 = _860 + _845;
                precise float _864 = uintBitsToFloat(srt_flatbuf_1.data[70u]) * (-_857);
                precise float _865 = _864 + _854;
                precise float _867 = uintBitsToFloat(srt_flatbuf_1.data[69u]) * _857;
                precise float _869 = uintBitsToFloat(srt_flatbuf_1.data[72u]) * fs_in_attr1.x;
                precise float _870 = _869 + _861;
                precise float _871 = (-2.0) * _865;
                precise float _872 = _871 + fs_in_attr1.x;
                precise float _874 = uintBitsToFloat(srt_flatbuf_1.data[70u]) * _870;
                precise float _877 = uintBitsToFloat(srt_flatbuf_1.data[71u]) * (-_870);
                precise float _878 = _877 + _867;
                precise float _880 = uintBitsToFloat(srt_flatbuf_1.data[68u]) * _872;
                precise float _881 = (-2.0) * _878;
                precise float _882 = _881 + fs_in_attr1.y;
                precise float _885 = uintBitsToFloat(srt_flatbuf_1.data[69u]) * (-_848);
                precise float _886 = _885 + _874;
                precise float _887 = _880 * _880;
                precise float _889 = uintBitsToFloat(srt_flatbuf_1.data[68u]) * _882;
                precise float _890 = (-2.0) * _886;
                precise float _891 = _890 + fs_in_attr1.z;
                precise float _892 = _889 * _889;
                precise float _893 = _892 + _887;
                precise float _895 = uintBitsToFloat(srt_flatbuf_1.data[68u]) * _891;
                precise float _896 = _895 * _895;
                precise float _897 = _896 + _893;
                float _898 = inversesqrt(_897);
                precise float _899 = _898 * _889;
                bool _903 = _739 && (1.4210854715202003717422485351562e-14 < _897);
                uint _904 = _903 ? floatBitsToUint(_899) : 0u;
                precise float _905 = _898 * _895;
                precise float _909 = (-1.02332675457000732421875) * uintBitsToFloat(_904);
                uint _910 = _903 ? floatBitsToUint(_905) : 0u;
                uint _911 = (_834 + 60u) >> 2u;
                uint _918 = (_834 + 72u) >> 2u;
                precise float _926 = _898 * _880;
                uint _928 = (_834 + 84u) >> 2u;
                precise float _937 = uintBitsToFloat(ssbo_2_1.data[_911]) * _909;
                precise float _940 = 1.02332675457000732421875 * uintBitsToFloat(_910);
                uint _941 = _903 ? floatBitsToUint(_926) : 0u;
                uint _942 = (_834 + 96u) >> 2u;
                uint _945 = _942 + 1u;
                precise float _949 = uintBitsToFloat(ssbo_2_1.data[_918]) * _940;
                precise float _950 = _949 + _937;
                precise float _952 = (-1.02332675457000732421875) * uintBitsToFloat(_941);
                precise float _955 = uintBitsToFloat(_941) * uintBitsToFloat(_904);
                precise float _959 = uintBitsToFloat(ssbo_2_1.data[_911 + 1u]) * _909;
                precise float _961 = 0.858085572719573974609375 * _955;
                uint _962 = (_834 + 108u) >> 2u;
                uint _965 = _962 + 1u;
                precise float _969 = uintBitsToFloat(ssbo_2_1.data[_918 + 1u]) * _940;
                precise float _970 = _969 + _959;
                precise float _972 = uintBitsToFloat(ssbo_2_1.data[_928]) * _952;
                precise float _973 = _972 + _950;
                precise float _975 = uintBitsToFloat(ssbo_2_1.data[_942]) * _961;
                precise float _976 = _975 + _973;
                precise float _978 = uintBitsToFloat(ssbo_2_1.data[_942]) * _961;
                precise float _980 = 0.10925485193729400634765625 * _955;
                precise float _983 = uintBitsToFloat(_904) * uintBitsToFloat(_910);
                precise float _987 = uintBitsToFloat(ssbo_2_1.data[_928 + 1u]) * _952;
                precise float _988 = _987 + _970;
                precise float _990 = (-0.858085572719573974609375) * _983;
                precise float _992 = uintBitsToFloat(ssbo_2_1.data[_945]) * _961;
                precise float _993 = _992 + _988;
                precise float _995 = uintBitsToFloat(ssbo_2_1.data[_945]) * _961;
                precise float _997 = _980 * (-_978);
                precise float _998 = _997 + _976;
                precise float _1000 = uintBitsToFloat(ssbo_2_1.data[_962]) * _990;
                precise float _1002 = (-0.10925485193729400634765625) * _983;
                uint _1003 = (_834 + 120u) >> 2u;
                uint _1006 = _1003 + 1u;
                precise float _1012 = uintBitsToFloat(ssbo_2_1.data[_962]) * _990;
                precise float _1013 = _1012 + _998;
                precise float _1015 = _980 * (-_995);
                precise float _1016 = _1015 + _993;
                precise float _1019 = uintBitsToFloat(_910) * uintBitsToFloat(_910);
                uint _1020 = (_834 + 132u) >> 2u;
                uint _1023 = _1020 + 1u;
                precise float _1029 = _1002 * (-_1000);
                precise float _1030 = _1029 + _1013;
                precise float _1032 = uintBitsToFloat(ssbo_2_1.data[_965]) * _990;
                precise float _1033 = _1032 + _1016;
                precise float _1035 = uintBitsToFloat(ssbo_2_1.data[_965]) * _990;
                precise float _1038 = fma(0.74312388896942138671875, _1019, -0.24770796298980712890625);
                precise float _1040 = _1002 * (-_1035);
                precise float _1041 = _1040 + _1033;
                precise float _1043 = uintBitsToFloat(ssbo_2_1.data[_1003]) * _1038;
                precise float _1044 = _1043 + _1030;
                precise float _1047 = uintBitsToFloat(_941) * uintBitsToFloat(_910);
                precise float _1049 = uintBitsToFloat(ssbo_2_1.data[_1003]) * _1038;
                precise float _1051 = fma(0.09461747109889984130859375, _1019, -0.24770796298980712890625);
                precise float _1052 = (-0.858085572719573974609375) * _1047;
                uint _1071 = (_834 + 104u) >> 2u;
                uint _1076 = (_834 + 116u) >> 2u;
                uint _1081 = (_834 + 128u) >> 2u;
                uint _1086 = (_834 + 140u) >> 2u;
                uint _1091 = (_834 + 152u) >> 2u;
                precise float _1095 = uintBitsToFloat(ssbo_2_1.data[_1006]) * _1038;
                precise float _1097 = uintBitsToFloat(ssbo_2_1.data[_1006]) * _1038;
                precise float _1098 = _1097 + _1041;
                precise float _1100 = uintBitsToFloat(ssbo_2_1.data[(_834 + 68u) >> 2u]) * _909;
                precise float _1102 = uintBitsToFloat(ssbo_2_1.data[(_834 + 80u) >> 2u]) * _940;
                precise float _1103 = _1102 + _1100;
                precise float _1105 = uintBitsToFloat(ssbo_2_1.data[(_834 + 92u) >> 2u]) * _952;
                precise float _1106 = _1105 + _1103;
                precise float _1108 = uintBitsToFloat(ssbo_2_1.data[_1071]) * _961;
                precise float _1110 = uintBitsToFloat(ssbo_2_1.data[_1071]) * _961;
                precise float _1111 = _1110 + _1106;
                precise float _1113 = _980 * (-_1108);
                precise float _1114 = _1113 + _1111;
                precise float _1116 = uintBitsToFloat(ssbo_2_1.data[_1076]) * _990;
                precise float _1118 = uintBitsToFloat(ssbo_2_1.data[_1076]) * _990;
                precise float _1119 = _1118 + _1114;
                precise float _1121 = _1002 * (-_1116);
                precise float _1122 = _1121 + _1119;
                precise float _1125 = uintBitsToFloat(_941) * uintBitsToFloat(_941);
                precise float _1127 = uintBitsToFloat(ssbo_2_1.data[_1081]) * _1038;
                precise float _1128 = _1127 + _1122;
                precise float _1130 = uintBitsToFloat(ssbo_2_1.data[_1081]) * _1038;
                precise float _1132 = uintBitsToFloat(ssbo_2_1.data[_1020]) * _1052;
                uint _1133 = (_834 + 144u) >> 2u;
                uint _1136 = _1133 + 1u;
                precise float _1142 = _1051 * (-_1049);
                precise float _1143 = _1142 + _1044;
                precise float _1147 = (-uintBitsToFloat(_904)) * uintBitsToFloat(_904);
                precise float _1148 = _1147 + _1125;
                precise float _1150 = _1051 * (-_1130);
                precise float _1151 = _1150 + _1128;
                precise float _1153 = _1051 * (-_1095);
                precise float _1154 = _1153 + _1098;
                precise float _1155 = (-0.10925485193729400634765625) * _1047;
                uint _1156 = (_834 + 48u) >> 2u;
                uint _1159 = _1156 + 1u;
                precise float _1163 = uintBitsToFloat(ssbo_2_1.data[_1086]) * _1052;
                precise float _1164 = _1163 + _1151;
                precise float _1166 = uintBitsToFloat(ssbo_2_1.data[_1086]) * _1052;
                uint _1167 = (_834 + 56u) >> 2u;
                precise float _1171 = uintBitsToFloat(ssbo_2_1.data[_1020]) * _1052;
                precise float _1172 = _1171 + _1143;
                precise float _1174 = uintBitsToFloat(ssbo_2_1.data[_1023]) * _1052;
                precise float _1175 = _1174 + _1154;
                precise float _1177 = uintBitsToFloat(ssbo_2_1.data[_1023]) * _1052;
                precise float _1179 = _1155 * (-_1132);
                precise float _1180 = _1179 + _1172;
                precise float _1182 = 0.4290427863597869873046875 * _1148;
                precise float _1184 = uintBitsToFloat(ssbo_2_1.data[_1091]) * _1182;
                precise float _1186 = _1155 * (-_1166);
                precise float _1187 = _1186 + _1164;
                precise float _1189 = _1155 * (-_1177);
                precise float _1190 = _1189 + _1175;
                precise float _1192 = uintBitsToFloat(ssbo_2_1.data[_1133]) * _1182;
                precise float _1194 = 0.054627425968647003173828125 * _1148;
                precise float _1196 = uintBitsToFloat(ssbo_2_1.data[_1133]) * _1182;
                precise float _1197 = _1196 + _1180;
                precise float _1199 = uintBitsToFloat(ssbo_2_1.data[_1091]) * _1182;
                precise float _1200 = _1199 + _1187;
                precise float _1202 = uintBitsToFloat(ssbo_2_1.data[_1136]) * _1182;
                precise float _1203 = _1202 + _1190;
                precise float _1205 = _1194 * (-_1192);
                precise float _1206 = _1205 + _1197;
                precise float _1208 = _1194 * (-_1184);
                precise float _1209 = _1208 + _1200;
                precise float _1211 = uintBitsToFloat(ssbo_2_1.data[_1136]) * _1182;
                precise float _1213 = _1194 * (-_1211);
                precise float _1214 = _1213 + _1203;
                precise float _1216 = (-0.25) + _1206;
                precise float _1219 = 0.88622701168060302734375 * uintBitsToFloat(ssbo_2_1.data[_1156]);
                precise float _1220 = (-0.25) + _1209;
                precise float _1222 = 0.88622701168060302734375 * uintBitsToFloat(ssbo_2_1.data[_1167]);
                precise float _1223 = (-0.25) + _1214;
                precise float _1225 = 0.88622701168060302734375 * uintBitsToFloat(ssbo_2_1.data[_1159]);
                precise float _1227 = _1219 * 0.71790516376495361328125;
                precise float _1228 = _1227 + _1216;
                precise float _1229 = _1222 * 0.71790516376495361328125;
                precise float _1230 = _1229 + _1220;
                precise float _1231 = _1225 * 0.71790516376495361328125;
                precise float _1232 = _1231 + _1223;
                precise float _1237 = 1.25 * max(0.0, _1228);
                precise float _1238 = 1.25 * max(0.0, _1230);
                precise float _1239 = 1.25 * max(0.0, _1232);
                precise float _1242 = 0.88622701168060302734375 * uintBitsToFloat(ssbo_2_1.data[_1156]);
                precise float _1243 = _1242 + (-_1237);
                precise float _1246 = 0.88622701168060302734375 * uintBitsToFloat(ssbo_2_1.data[_1167]);
                precise float _1247 = _1246 + (-_1238);
                precise float _1250 = 0.88622701168060302734375 * uintBitsToFloat(ssbo_2_1.data[_1159]);
                precise float _1251 = _1250 + (-_1239);
                precise float _1253 = _1243 * 0.20000000298023223876953125;
                precise float _1254 = _1253 + _1237;
                precise float _1255 = _1247 * 0.20000000298023223876953125;
                precise float _1256 = _1255 + _1238;
                precise float _1257 = _1251 * 0.20000000298023223876953125;
                precise float _1258 = _1257 + _1239;
                float _1260 = max3(_1254, _1258, _1256);
                precise float _1262 = 9.9999996826552253889678874634872e-21 + _1260;
                float _1265 = max(_806, _808);
                float _1268 = min(_804, _1265);
                float _1269 = max3(_804, _806, _808);
                uint _1270 = floatBitsToUint(_1269);
                precise float _1271 = (1.0 / _1262) * _1260;
                precise float _1272 = _1260 - min3(max(_1258, _1256), min(_1254, _1258), _1256);
                precise float _1274 = 9.9999996826552253889678874634872e-21 + _1269;
                precise float _1275 = _1271 * _1272;
                float _1276 = clamp(_1275, 0.0, 1.0);
                precise float _1277 = _1269 - min3(_1268, _806, _808);
                precise float _1279 = _1276 * _1276;
                precise float _1280 = (1.0 / _1274) * _1277;
                precise float _1281 = _1279 * _1280;
                precise float _1282 = (-0.5) * _1281;
                precise float _1283 = _1282 + _1280;
                uvec4 _1289 = subgroupBallot(_739);
                bool _1292 = _739 && (_739 && (0.0 != _1283));
                uint _1455;
                uint _1456;
                uint _1457;
                if (_1292)
                {
                    bool _1294 = _1292 && (_806 < _808);
                    float _1302 = float(int(6u));
                    precise float _1306 = _1268 - min(_806, _808);
                    precise float _1308 = _1306 * (1.0 / fma(_1302, _1277, 9.9999996826552253889678874634872e-21));
                    precise float _1309 = _1308 + uintBitsToFloat((_1292 && (_804 < _1265)) ? (_1294 ? 1059760810u : 3198855851u) : (_1294 ? 3212836864u : 0u));
                    float _1311 = fract(abs(_1309));
                    precise float _1313 = 6.0 * _1311;
                    precise float _1316 = _1311 * 6.0;
                    precise float _1317 = _1316 + trunc(-_1313);
                    precise float _1319 = _1317 * _1283;
                    precise float _1320 = _1319 + (-_1283);
                    uint _1321 = uint(int(_1313));
                    precise float _1323 = (-_1283) * _1269;
                    precise float _1324 = _1269 * _1320;
                    precise float _1325 = _1324 + _1269;
                    uint _1326 = floatBitsToUint(_1325);
                    uvec4 _1329 = subgroupBallot(_1292 && (0u == _1321));
                    uint _1330 = _1329.x;
                    uint _1331 = _1329.y;
                    uvec4 _1334 = subgroupBallot(_1292 && (1u == _1321));
                    precise float _1337 = _1323 * _1317;
                    precise float _1338 = _1337 + _1269;
                    uint _1339 = floatBitsToUint(_1338);
                    bool _1341 = _1292 && (4u == _1321);
                    uint _1343 = gl_SubgroupInvocationID & 63u;
                    uvec4 _1353 = subgroupBallot(_1292 && (2u == _1321));
                    precise float _1357 = (-_1283) * _1269;
                    precise float _1358 = _1357 + _1269;
                    uint _1359 = floatBitsToUint(_1358);
                    uint _1361 = gl_SubgroupInvocationID & 63u;
                    uvec4 _1371 = subgroupBallot(_1292 && (3u == _1321));
                    uint _1377 = gl_SubgroupInvocationID & 63u;
                    uint _1385 = gl_SubgroupInvocationID & 63u;
                    bool _1392 = (((((_1377 >= 32u) ? _1334.y : _1334.x) >> (_1377 & 31u)) & 1u) != 0u) || (((((_1385 >= 32u) ? _1331 : _1330) >> (_1385 & 31u)) & 1u) != 0u);
                    uint _1395 = gl_SubgroupInvocationID & 63u;
                    uvec4 _1403 = subgroupBallot((((((_1395 >= 32u) ? _1353.y : _1353.x) >> (_1395 & 31u)) & 1u) != 0u) || _1392);
                    uint _1404 = _1403.x;
                    uint _1405 = _1403.y;
                    uint _1409 = gl_SubgroupInvocationID & 63u;
                    uint _1418 = gl_SubgroupInvocationID & 63u;
                    uint _1426 = gl_SubgroupInvocationID & 63u;
                    bool _1433 = (((((_1418 >= 32u) ? _1371.y : _1371.x) >> (_1418 & 31u)) & 1u) != 0u) || (((((_1426 >= 32u) ? _1405 : _1404) >> (_1426 & 31u)) & 1u) != 0u);
                    uint _1435 = gl_SubgroupInvocationID & 63u;
                    uint _1444 = gl_SubgroupInvocationID & 63u;
                    _1455 = _1433 ? ((((((_1444 >= 32u) ? _1405 : _1404) >> (_1444 & 31u)) & 1u) != 0u) ? (_1392 ? _1359 : _1326) : _1270) : (_1341 ? _1270 : _1339);
                    _1456 = _1433 ? ((((((_1409 >= 32u) ? _1405 : _1404) >> (_1409 & 31u)) & 1u) != 0u) ? (_1392 ? ((((((_1343 >= 32u) ? _1331 : _1330) >> (_1343 & 31u)) & 1u) != 0u) ? _1326 : _1270) : _1270) : _1339) : _1359;
                    _1457 = _1433 ? ((((((_1435 >= 32u) ? _1405 : _1404) >> (_1435 & 31u)) & 1u) != 0u) ? (_1392 ? ((((((_1361 >= 32u) ? _1331 : _1330) >> (_1361 & 31u)) & 1u) != 0u) ? _1270 : _1339) : _1359) : _1359) : (_1341 ? _1326 : _1270);
                }
                else
                {
                    _1455 = _1270;
                    _1456 = floatBitsToUint(_1269);
                    _1457 = floatBitsToUint(_1269);
                }
                uint _1459 = gl_SubgroupInvocationID & 63u;
                precise float _1466 = 0.0039215688593685626983642578125 * _817;
                precise float _1468 = uintBitsToFloat(ssbo_2_1.data[_780]) * _1466;
                precise float _1471 = uintBitsToFloat(_1457) * _1254;
                precise float _1472 = _1471 + (-_804);
                precise float _1475 = uintBitsToFloat(_1456) * _1258;
                precise float _1476 = _1475 + (-_806);
                precise float _1479 = uintBitsToFloat(_1455) * _1256;
                precise float _1480 = _1479 + (-_808);
                precise float _1481 = _1472 * _1468;
                precise float _1482 = _1481 + _804;
                precise float _1484 = _1476 * _1468;
                precise float _1485 = _1484 + _806;
                precise float _1487 = _1480 * _1468;
                precise float _1488 = _1487 + _808;
                _1490 = floatBitsToUint(_1488);
                _1491 = floatBitsToUint(_1485);
                _1492 = floatBitsToUint(_1482);
                _1493 = ((((_1459 >= 32u) ? _1289.y : _1289.x) >> (_1459 & 31u)) & 1u) != 0u;
            }
            else
            {
                _1490 = floatBitsToUint(_808);
                _1491 = floatBitsToUint(_806);
                _1492 = floatBitsToUint(_804);
                _1493 = _739;
            }
            uint _1497 = 255u & floatBitsToUint(_131.z);
            uvec4 _1500 = subgroupBallot(_1493 && (255u == _1497));
            uint _1506 = gl_SubgroupInvocationID & 63u;
            uvec4 _1515 = subgroupBallot(_1493);
            bool _1518 = _1493 && (!((((((_1506 >= 32u) ? _1500.y : _1500.x) >> (_1506 & 31u)) & 1u) != 0u) || (_1493 && (0.0 >= _817))));
            uint _2187;
            uint _2188;
            uint _2189;
            if (_1518)
            {
                uint _1520 = srt_flatbuf_1.data[64u] * 200u;
                uint _1521 = _1520 + _1497;
                uint _1523 = (_1521 + 1u) * 4u;
                uvec4 _1535 = uvec4(ssbo_3_1.data[_1523], ssbo_3_1.data[_1523 + 1u], ssbo_3_1.data[_1523 + 2u], ssbo_3_1.data[_1523 + 3u]);
                uint _1539 = _1535.w;
                uint _1540 = _1521 * 4u;
                uvec4 _1552 = uvec4(ssbo_3_1.data[_1540], ssbo_3_1.data[_1540 + 1u], ssbo_3_1.data[_1540 + 2u], ssbo_3_1.data[_1540 + 3u]);
                uint _1553 = _1552.x;
                uint _1554 = _1552.y;
                uint _1555 = _1552.z;
                uint _1556 = _1552.w;
                uint _1557 = srt_flatbuf_1.data[64u] * 208u;
                uint _1566 = (_1557 + 16u) >> 2u;
                uint _1572 = (_1557 + 168u) >> 2u;
                uint _1581 = _1572 + 3u;
                uint _1591 = _1572 + 6u;
                uint _1595 = _1572 + 7u;
                uint _1598 = (_1520 << 4u) >> 2u;
                uint _1601 = _1598 + 1u;
                uint _1604 = _1598 + 2u;
                precise float _1613 = uintBitsToFloat(_1539) - uintBitsToFloat(_1556);
                uint _1631;
                uint _1632;
                uint _1633;
                if (_1518 && (_1518 && (uintBitsToFloat(_1539) > uintBitsToFloat(_1556))))
                {
                    precise float _1617 = uintBitsToFloat(_1535.x) - uintBitsToFloat(_1553);
                    float _1618 = 1.0 / _1613;
                    precise float _1621 = uintBitsToFloat(_1535.y) - uintBitsToFloat(_1554);
                    precise float _1624 = uintBitsToFloat(_1535.z) - uintBitsToFloat(_1555);
                    precise float _1625 = _1618 * _1617;
                    precise float _1627 = _1618 * _1621;
                    precise float _1629 = _1618 * _1624;
                    _1631 = floatBitsToUint(_1629);
                    _1632 = floatBitsToUint(_1627);
                    _1633 = floatBitsToUint(_1625);
                }
                else
                {
                    _1631 = 0u;
                    _1632 = 0u;
                    _1633 = 0u;
                }
                precise float _1635 = fs_in_attr1.x - uintBitsToFloat(_1553);
                precise float _1637 = uintBitsToFloat(_1633) * _1635;
                precise float _1639 = fs_in_attr1.y - uintBitsToFloat(_1554);
                precise float _1641 = uintBitsToFloat(_1632) * _1639;
                precise float _1642 = _1641 + _1637;
                precise float _1644 = fs_in_attr1.z - uintBitsToFloat(_1555);
                precise float _1646 = _1644 * uintBitsToFloat(_1631);
                precise float _1647 = _1646 + _1642;
                precise float _1650 = _1647 * uintBitsToFloat(_1633);
                precise float _1651 = _1650 + uintBitsToFloat(_1553);
                precise float _1656 = _1647 * uintBitsToFloat(_1632);
                precise float _1657 = _1656 + uintBitsToFloat(_1554);
                precise float _1658 = fs_in_attr6.y - _1657;
                precise float _1663 = _1647 * uintBitsToFloat(_1631);
                precise float _1664 = _1663 + uintBitsToFloat(_1555);
                precise float _1665 = fs_in_attr6.z - _1664;
                precise float _1667 = uintBitsToFloat(_1556) + _1647;
                precise float _1670 = fs_in_attr6.x - _1651;
                precise float _1671 = _1670 * _1670;
                precise float _1672 = _1658 * _1658;
                precise float _1673 = _1672 + _1671;
                precise float _1674 = _1665 * _1665;
                precise float _1675 = _1674 + _1673;
                float _1676 = max(0.0, _1667);
                float _1679 = min(0.0187500007450580596923828125, uintBitsToFloat(ssbo_2_1.data[_1595]));
                float _1680 = inversesqrt(_1675);
                precise float _1681 = _1680 * _1670;
                bool _1684 = _1518 && (1.4210854715202003717422485351562e-14 < _1675);
                precise float _1686 = _1679 - uintBitsToFloat(ssbo_2_1.data[_1595]);
                precise float _1687 = _1680 * _1665;
                precise float _1689 = _1680 * _1658;
                uint _1691 = _1684 ? floatBitsToUint(_1681) : 0u;
                precise float _1694 = uintBitsToFloat(ssbo_2_1.data[_1572 + 1u]) + uintBitsToFloat(ssbo_2_1.data[_1572]);
                precise float _1697 = (1.0 / (-_1694)) * _1676;
                precise float _1698 = _1697 + 1.0;
                float _1699 = clamp(_1698, 0.0, 1.0);
                precise float _1700 = _1699 * _1699;
                precise float _1702 = _1700 * (-_1699);
                precise float _1703 = _1702 + 1.0;
                precise float _1704 = 1.0 - _1703;
                precise float _1706 = (-_1704) * _1704;
                uint _1707 = _1684 ? floatBitsToUint(_1689) : 0u;
                uint _1708 = _1684 ? floatBitsToUint(_1687) : 0u;
                precise float _1709 = fs_in_attr1.z - fs_in_attr6.z;
                precise float _1710 = _1706 * _1686;
                precise float _1711 = _1710 + _1679;
                precise float _1712 = fs_in_attr1.x - fs_in_attr6.x;
                precise float _1716 = uintBitsToFloat(_1691) * _1712;
                precise float _1717 = (1.0 / uintBitsToFloat(ssbo_2_1.data[_1572 + 2u])) * _1676;
                precise float _1719 = fs_in_attr1.y - fs_in_attr6.y;
                precise float _1721 = _1719 * uintBitsToFloat(_1707);
                precise float _1722 = _1721 + _1716;
                precise float _1724 = _1709 * uintBitsToFloat(_1708);
                precise float _1725 = _1724 + _1722;
                uint _1756;
                uint _1757;
                uint _1758;
                if (_1518 && (_1518 && (abs(_1725) > 0.001000000047497451305389404296875)))
                {
                    precise float _1734 = _1651 - fs_in_attr6.x;
                    precise float _1736 = uintBitsToFloat(_1691) * _1734;
                    precise float _1737 = _1657 - fs_in_attr6.y;
                    precise float _1739 = _1737 * uintBitsToFloat(_1707);
                    precise float _1740 = _1739 + _1736;
                    precise float _1741 = _1664 - fs_in_attr6.z;
                    precise float _1744 = _1741 * uintBitsToFloat(_1708);
                    precise float _1745 = _1744 + _1740;
                    precise float _1746 = (1.0 / _1725) * _1745;
                    precise float _1747 = _1712 * _1746;
                    precise float _1748 = _1747 + fs_in_attr6.x;
                    precise float _1750 = _1719 * _1746;
                    precise float _1751 = _1750 + fs_in_attr6.y;
                    precise float _1753 = _1709 * _1746;
                    precise float _1754 = _1753 + fs_in_attr6.z;
                    _1756 = floatBitsToUint(_1754);
                    _1757 = floatBitsToUint(_1751);
                    _1758 = floatBitsToUint(_1748);
                }
                else
                {
                    _1756 = floatBitsToUint(fs_in_attr1.z);
                    _1757 = floatBitsToUint(fs_in_attr1.y);
                    _1758 = floatBitsToUint(fs_in_attr1.x);
                }
                precise float _1760 = uintBitsToFloat(_1758) - _1651;
                precise float _1761 = _1760 * _1760;
                precise float _1763 = uintBitsToFloat(_1757) - _1657;
                precise float _1765 = uintBitsToFloat(_1756) - _1664;
                precise float _1766 = _1763 * _1763;
                precise float _1767 = _1766 + _1761;
                precise float _1768 = _1765 * _1765;
                precise float _1769 = _1768 + _1767;
                precise float _1772 = uintBitsToFloat(ssbo_2_1.data[_1591]) - _1711;
                precise float _1773 = sqrt(_1769) - _1711;
                precise float _1775 = 0.1500000059604644775390625 - _1679;
                uvec4 _1778 = subgroupBallot(_1518 && (0u != _1497));
                float _1782 = max(0.0, _1772);
                precise float _1784 = min(_1782, _1775) - _1782;
                precise float _1785 = _1784 * _1703;
                precise float _1786 = _1785 + _1782;
                precise float _1790 = fs_in_attr6.x - uintBitsToFloat(ssbo_3_1.data[_1598]);
                precise float _1792 = _1790 * _1790;
                precise float _1794 = fs_in_attr6.z - uintBitsToFloat(ssbo_3_1.data[_1604]);
                precise float _1795 = (1.0 / max(9.9999997473787516355514526367188e-05, _1786)) * max(0.0, _1773);
                precise float _1798 = fs_in_attr6.y - uintBitsToFloat(ssbo_3_1.data[_1601]);
                precise float _1799 = _1798 * _1798;
                precise float _1800 = _1799 + _1792;
                precise float _1801 = _1794 * _1794;
                precise float _1802 = _1801 + _1800;
                float _1803 = inversesqrt(_1802);
                precise float _1804 = _1803 * _1790;
                bool _1807 = _1518 && (1.4210854715202003717422485351562e-14 < _1802);
                precise float _1808 = _1803 * _1798;
                precise float _1810 = _1803 * _1794;
                uint _1812 = _1807 ? floatBitsToUint(_1804) : 0u;
                precise float _1814 = uintBitsToFloat(_1812) * _1712;
                uint _1815 = _1807 ? floatBitsToUint(_1808) : 0u;
                uint _1816 = _1807 ? floatBitsToUint(_1810) : 0u;
                precise float _1821 = _1719 * uintBitsToFloat(_1815);
                precise float _1822 = _1821 + _1814;
                precise float _1824 = uintBitsToFloat(_1816) * _1709;
                precise float _1825 = _1824 + _1822;
                uvec4 _1829 = subgroupBallot(_1518 && (abs(_1825) > 0.001000000047497451305389404296875));
                uint _1836 = gl_SubgroupInvocationID & 63u;
                float _1845 = float(uint((_1518 && (uintBitsToFloat(ssbo_3_1.data[_1601]) <= fs_in_attr1.y)) || (((((_1836 >= 32u) ? _1778.y : _1778.x) >> (_1836 & 31u)) & 1u) != 0u)));
                precise float _1847 = _1845 * (-clamp(_1795, 0.0, 1.0));
                precise float _1848 = _1847 + _1845;
                uint _1850 = gl_SubgroupInvocationID & 63u;
                uint _1883;
                uint _1884;
                uint _1885;
                if (_1518 && (((((_1850 >= 32u) ? _1829.y : _1829.x) >> (_1850 & 31u)) & 1u) != 0u))
                {
                    precise float _1859 = uintBitsToFloat(ssbo_3_1.data[_1598]) - fs_in_attr6.x;
                    precise float _1861 = uintBitsToFloat(_1812) * _1859;
                    precise float _1863 = uintBitsToFloat(ssbo_3_1.data[_1601]) - fs_in_attr6.y;
                    precise float _1865 = uintBitsToFloat(ssbo_3_1.data[_1604]) - fs_in_attr6.z;
                    precise float _1867 = _1863 * uintBitsToFloat(_1815);
                    precise float _1868 = _1867 + _1861;
                    precise float _1870 = _1865 * uintBitsToFloat(_1816);
                    precise float _1871 = _1870 + _1868;
                    precise float _1873 = (1.0 / _1825) * _1871;
                    precise float _1874 = _1712 * _1873;
                    precise float _1875 = _1874 + fs_in_attr6.x;
                    precise float _1877 = _1719 * _1873;
                    precise float _1878 = _1877 + fs_in_attr6.y;
                    precise float _1880 = _1709 * _1873;
                    precise float _1881 = _1880 + fs_in_attr6.z;
                    _1883 = floatBitsToUint(_1881);
                    _1884 = floatBitsToUint(_1878);
                    _1885 = floatBitsToUint(_1875);
                }
                else
                {
                    _1883 = floatBitsToUint(fs_in_attr1.z);
                    _1884 = floatBitsToUint(fs_in_attr1.y);
                    _1885 = floatBitsToUint(fs_in_attr1.x);
                }
                precise float _1888 = uintBitsToFloat(_1885) - uintBitsToFloat(ssbo_3_1.data[_1598]);
                precise float _1889 = _1888 * _1888;
                precise float _1892 = uintBitsToFloat(_1884) - uintBitsToFloat(ssbo_3_1.data[_1601]);
                precise float _1893 = _1892 * _1892;
                precise float _1894 = _1893 + _1889;
                precise float _1897 = uintBitsToFloat(_1883) - uintBitsToFloat(ssbo_3_1.data[_1604]);
                precise float _1898 = _1897 * _1897;
                precise float _1899 = _1898 + _1894;
                precise float _1903 = uintBitsToFloat(ssbo_2_1.data[_1591]) - uintBitsToFloat(ssbo_2_1.data[_1595]);
                precise float _1905 = sqrt(_1899) - uintBitsToFloat(ssbo_2_1.data[_1595]);
                precise float _1910 = (1.0 / (-max(9.9999997473787516355514526367188e-05, _1903))) * max(0.0, _1905);
                precise float _1911 = _1910 + 1.0;
                float _1912 = clamp(_1911, 0.0, 1.0);
                precise float _1913 = _1848 * _1848;
                precise float _1914 = _1912 * _1912;
                precise float _1915 = _1913 * _1848;
                float _1916 = clamp(_1915, 0.0, 1.0);
                precise float _1917 = _1914 * _1912;
                float _1918 = clamp(_1917, 0.0, 1.0);
                precise float _1921 = _1916 * _1916;
                precise float _1923 = _1918 * _1918;
                precise float _1924 = _1921 * fma(-2.0, _1916, 3.0);
                precise float _1928 = _1923 * fma(-2.0, _1918, 3.0);
                precise float _1930 = 0.4000000059604644775390625 * _1924;
                precise float _1933 = uintBitsToFloat(ssbo_2_1.data[_1572 + 4u]) - uintBitsToFloat(ssbo_2_1.data[_1581]);
                uint _1934 = ((srt_flatbuf_1.data[64u] * 208u) + 28u) >> 2u;
                precise float _1939 = clamp(_1717, 0.0, 1.0) * _1933;
                precise float _1940 = _1939 + uintBitsToFloat(ssbo_2_1.data[_1581]);
                precise float _1943 = max(_1930, _1928) * _1940;
                uint _1944 = floatBitsToUint(_1943);
                float _1945 = 1.0 / max(9.9999997473787516355514526367188e-05, uintBitsToFloat(ssbo_2_1.data[_1591]));
                uint _1946 = srt_flatbuf_1.data[64u] << 5u;
                uint _2111;
                uint _2112;
                uint _2113;
                uint _1947 = _1944;
                uint _1948 = 0u;
                for (;;)
                {
                    if (!(_1948 < ssbo_2_1.data[_1934]))
                    {
                        _2113 = _1947;
                        break;
                    }
                    else
                    {
                        uint _1953 = (_1946 + _1948) * 24u;
                        uint _1955 = (_1953 + 16u) >> 2u;
                        uint _1961 = _1953 >> 2u;
                        uint _1964 = _1961 + 1u;
                        uint _1967 = _1961 + 2u;
                        precise float _1975 = fs_in_attr6.x - uintBitsToFloat(ssbo_1_1.data[_1961]);
                        precise float _1976 = _1975 * _1975;
                        precise float _1978 = fs_in_attr6.y - uintBitsToFloat(ssbo_1_1.data[_1964]);
                        precise float _1980 = fs_in_attr6.z - uintBitsToFloat(ssbo_1_1.data[_1967]);
                        precise float _1981 = _1978 * _1978;
                        precise float _1982 = _1981 + _1976;
                        precise float _1983 = _1980 * _1980;
                        precise float _1984 = _1983 + _1982;
                        float _1985 = inversesqrt(_1984);
                        precise float _1986 = _1985 * _1975;
                        bool _1989 = _1518 && (1.4210854715202003717422485351562e-14 < _1984);
                        uint _1990 = _1989 ? floatBitsToUint(_1986) : 0u;
                        precise float _1991 = _1985 * _1978;
                        precise float _1993 = _1985 * _1980;
                        uint _1995 = _1989 ? floatBitsToUint(_1991) : 0u;
                        precise float _1997 = uintBitsToFloat(_1990) * _1712;
                        precise float _1999 = uintBitsToFloat(_1995) * _1719;
                        precise float _2000 = _1999 + _1997;
                        uint _2001 = _1989 ? floatBitsToUint(_1993) : 0u;
                        precise float _2003 = _1709 * uintBitsToFloat(_2001);
                        precise float _2004 = _2003 + _2000;
                        precise float _2009 = _1676 - uintBitsToFloat(ssbo_1_1.data[_1955 + 1u]);
                        uint _2038;
                        uint _2039;
                        uint _2040;
                        if (_1518 && (_1518 && (abs(_2004) > 0.001000000047497451305389404296875)))
                        {
                            precise float _2014 = uintBitsToFloat(ssbo_1_1.data[_1961]) - fs_in_attr6.x;
                            precise float _2016 = uintBitsToFloat(_1990) * _2014;
                            precise float _2018 = uintBitsToFloat(ssbo_1_1.data[_1964]) - fs_in_attr6.y;
                            precise float _2020 = _2018 * uintBitsToFloat(_1995);
                            precise float _2021 = _2020 + _2016;
                            precise float _2023 = uintBitsToFloat(ssbo_1_1.data[_1967]) - fs_in_attr6.z;
                            precise float _2025 = _2023 * uintBitsToFloat(_2001);
                            precise float _2026 = _2025 + _2021;
                            precise float _2028 = (1.0 / _2004) * _2026;
                            precise float _2029 = _1719 * _2028;
                            precise float _2030 = _2029 + fs_in_attr6.y;
                            precise float _2032 = _1709 * _2028;
                            precise float _2033 = _2032 + fs_in_attr6.z;
                            precise float _2035 = _1712 * _2028;
                            precise float _2036 = _2035 + fs_in_attr6.x;
                            _2038 = floatBitsToUint(_2033);
                            _2039 = floatBitsToUint(_2030);
                            _2040 = floatBitsToUint(_2036);
                        }
                        else
                        {
                            _2038 = floatBitsToUint(fs_in_attr1.z);
                            _2039 = floatBitsToUint(fs_in_attr1.y);
                            _2040 = floatBitsToUint(fs_in_attr1.x);
                        }
                        precise float _2043 = uintBitsToFloat(_2040) - uintBitsToFloat(ssbo_1_1.data[_1961]);
                        precise float _2044 = _2043 * _2043;
                        precise float _2047 = uintBitsToFloat(_2039) - uintBitsToFloat(ssbo_1_1.data[_1964]);
                        precise float _2048 = _2047 * _2047;
                        precise float _2049 = _2048 + _2044;
                        precise float _2052 = uintBitsToFloat(_2038) - uintBitsToFloat(ssbo_1_1.data[_1967]);
                        precise float _2053 = _2052 * _2052;
                        precise float _2054 = _2053 + _2049;
                        float _2058 = min(uintBitsToFloat(ssbo_2_1.data[_1591]), uintBitsToFloat(ssbo_1_1.data[_1955]));
                        precise float _2059 = _1945 * _2058;
                        float _2060 = clamp(_2059, 0.0, 1.0);
                        precise float _2064 = (-uintBitsToFloat(ssbo_2_1.data[_1595])) * _2060;
                        precise float _2065 = _2064 + _2058;
                        precise float _2071 = (-uintBitsToFloat(ssbo_2_1.data[_1595])) * _2060;
                        precise float _2072 = _2071 + sqrt(_2054);
                        precise float _2076 = (1.0 / (-max(9.9999997473787516355514526367188e-05, _2065))) * max(0.0, _2072);
                        precise float _2077 = _2076 + 1.0;
                        uint _2088;
                        uint _2089;
                        if (_1518 && (_1518 && (0.0 > _2009)))
                        {
                            precise float _2082 = (1.0 / (-_2009)) * _1676;
                            precise float _2084 = _2060 * clamp(_2082, 0.0, 1.0);
                            _2088 = floatBitsToUint(_2084);
                            _2089 = floatBitsToUint(-_2009);
                        }
                        else
                        {
                            _2088 = floatBitsToUint(_2060);
                            _2089 = floatBitsToUint(_2009);
                        }
                        precise float _2093 = uintBitsToFloat(_2089) * (1.0 / uintBitsToFloat(ssbo_1_1.data[_1955]));
                        precise float _2096 = (-clamp(_2093, 0.0, 1.0)) * _1848;
                        precise float _2097 = _2096 + _1848;
                        precise float _2099 = uintBitsToFloat(_2088) * _2097;
                        float _2100 = max(clamp(_2077, 0.0, 1.0), _2099);
                        precise float _2101 = _2100 * _2100;
                        precise float _2102 = _2101 * _2100;
                        float _2103 = clamp(_2102, 0.0, 1.0);
                        precise float _2104 = _2103 * _2103;
                        precise float _2106 = uintBitsToFloat(ssbo_1_1.data[_1961 + 3u]) * _2104;
                        precise float _2108 = _2106 * fma(-2.0, _2103, 3.0);
                        _2111 = floatBitsToUint(max(uintBitsToFloat(_1947), _2108));
                        _2112 = _1948 + 1u;
                        if (true)
                        {
                            _1947 = _2111;
                            _1948 = _2112;
                            continue;
                        }
                        else
                        {
                            _2113 = _2111;
                            break;
                        }
                    }
                }
                precise float _2114 = fs_in_attr1.x - _1651;
                precise float _2115 = _2114 * _2114;
                precise float _2116 = fs_in_attr1.y - _1657;
                precise float _2117 = fs_in_attr1.z - _1664;
                precise float _2118 = _2116 * _2116;
                precise float _2119 = _2118 + _2115;
                precise float _2122 = _2117 * _2117;
                precise float _2123 = _2122 + _2119;
                float _2124 = sqrt(_2123);
                precise float _2126 = fs_in_attr2.w * (-_2124);
                precise float _2127 = _2126 + fs_in_attr2.w;
                uint _2140;
                if (_1518 && (_1518 && (0u == _367)))
                {
                    precise float _2131 = _2114 * uintBitsToFloat(_1691);
                    precise float _2133 = uintBitsToFloat(_1707) * _2116;
                    precise float _2134 = _2133 + _2131;
                    precise float _2136 = uintBitsToFloat(_1708) * _2117;
                    precise float _2137 = _2136 + _2134;
                    _2140 = floatBitsToUint(abs(_2137));
                }
                else
                {
                    _2140 = floatBitsToUint(_2127);
                }
                precise float _2147 = uintBitsToFloat(_2140) * (1.0 / max(9.9999997473787516355514526367188e-05, _2124));
                precise float _2151 = uintBitsToFloat(_2140) * (1.0 / fma(-0.762499988079071044921875, _1703, 0.800000011920928955078125));
                precise float _2154 = 0.75 * clamp(_2147, 0.0, 1.0);
                precise float _2156 = _2154 + 0.25;
                precise float _2159 = clamp(_2151, 0.0, 1.0) * (-0.75);
                precise float _2160 = _2159 + clamp(_2156, 0.0, 1.0);
                precise float _2161 = fma(_2160, 0.5, 0.5);
                precise float _2162 = _2161 * _2161;
                precise float _2163 = _2162 * _2162;
                precise float _2165 = uintBitsToFloat(ssbo_2_1.data[_1572 + 5u]) * _2163;
                precise float _2168 = uintBitsToFloat(ssbo_2_1.data[_1566]) * uintBitsToFloat(_2113);
                precise float _2171 = uintBitsToFloat(ssbo_2_1.data[_1566 + 1u]) * uintBitsToFloat(_2113);
                precise float _2174 = uintBitsToFloat(ssbo_2_1.data[(_1557 + 24u) >> 2u]) * uintBitsToFloat(_2113);
                precise float _2176 = _2165 * _2168;
                precise float _2177 = _2176 + uintBitsToFloat(_1492);
                precise float _2180 = _2165 * _2171;
                precise float _2181 = _2180 + uintBitsToFloat(_1491);
                precise float _2184 = _2165 * _2174;
                precise float _2185 = _2184 + uintBitsToFloat(_1490);
                _2187 = floatBitsToUint(_2177);
                _2188 = floatBitsToUint(_2185);
                _2189 = floatBitsToUint(_2181);
            }
            else
            {
                _2187 = _1492;
                _2188 = _1490;
                _2189 = _1491;
            }
            uint _2191 = gl_SubgroupInvocationID & 63u;
            bool _2197 = ((((_2191 >= 32u) ? _1515.y : _1515.x) >> (_2191 & 31u)) & 1u) != 0u;
            uint _2208 = (_2197 && (16777215u < _643)) ? _585 : floatBitsToUint(fma(0.699999988079071044921875, uintBitsToFloat(_585), 0.300000011920928955078125));
            precise float _2211 = uintBitsToFloat(_585) * uintBitsToFloat(_2189);
            precise float _2214 = uintBitsToFloat(_585) * uintBitsToFloat(_2188);
            precise float _2217 = uintBitsToFloat(_585) * uintBitsToFloat(_2187);
            precise float _2219 = 4.0 * fs_in_attr0.x;
            precise float _2223 = _2211 * uintBitsToFloat(_2208);
            precise float _2225 = _2214 * uintBitsToFloat(_2208);
            precise float _2227 = _2217 * uintBitsToFloat(_2208);
            precise float _2230 = 4.0 * fs_in_attr0.y;
            uint _2233 = floatBitsToUint(mid3(65408.0, _2223, 0.0));
            uint _2235 = floatBitsToUint(mid3(65408.0, _2225, 0.0));
            uint _2237 = floatBitsToUint(mid3(65408.0, _2227, 0.0));
            uint _2242 = bitfieldExtract(_2233, int(23u), int(8u));
            uint _2243 = bitfieldExtract(_2235, int(23u), int(8u));
            uint _2244 = bitfieldExtract(_2237, int(23u), int(8u));
            precise float _2246 = 511.0 * sqrt(min(1.0, abs(_2219)));
            precise float _2247 = _2246 + 0.5;
            uint _2249 = max3(_2243, _2244, _2242);
            uint _2253 = uint(_2247);
            precise float _2254 = 511.0 * sqrt(min(1.0, abs(_2230)));
            precise float _2255 = _2254 + 0.5;
            uvec4 _2268 = subgroupBallot(_2197 && (0.0 > fs_in_attr0.x));
            uint _2271 = uint(_2255);
            uint _2281 = gl_SubgroupInvocationID & 63u;
            uint _2302;
            if (_2197 && (_2197 && (0.0 > fs_in_attr0.y)))
            {
                _2302 = 512u | _2271;
            }
            else
            {
                _2302 = _2271;
            }
            precise float _2317 = 255.0 * uintBitsToFloat(_2208);
            precise float _2318 = _2317 + 0.5;
            uint _2326 = gl_SubgroupInvocationID & 63u;
            if (!(((((_2326 >= 32u) ? _716.y : _717) >> (_2326 & 31u)) & 1u) != 0u))
            {
                demote;
            }
            frag_color0.x = floatBitsToUint(uintBitsToFloat(((((8388608u | (8388607u & _2237)) >> (min(24u, ((15u - _2244) + _2249)) & 31u)) | (mid3(31u, _2249 + 4294967185u, 0u) << 27u)) | (((8388608u | (8388607u & _2235)) >> (min(24u, ((15u - _2243) + _2249)) & 31u)) << 18u)) | (((8388608u | (8388607u & _2233)) >> (min(24u, ((15u - _2242) + _2249)) & 31u)) << 9u)));
            frag_color0.y = floatBitsToUint(uintBitsToFloat(bitfieldInsert((2147483648u | (((((((_2281 >= 32u) ? _2268.y : _2268.x) >> (_2281 & 31u)) & 1u) != 0u) ? (512u | _2253) : _2253) << 8u)) | (_2302 << 18u), uint(isnan(_2318) ? 0.0 : clamp(_2318, 0.0, 255.0)), int(0u), int(8u))));
            return;
        }
    }
    demote;
}

