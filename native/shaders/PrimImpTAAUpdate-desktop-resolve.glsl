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
#extension GL_EXT_samplerless_texture_functions : require
#extension GL_KHR_shader_subgroup_ballot : require
#extension GL_KHR_shader_subgroup_basic : require
#extension GL_AMD_shader_trinary_minmax : require
layout(local_size_x = 64, local_size_y = 1, local_size_z = 1) in;

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

layout(set = 0, binding = 0, std430) readonly buffer srt_flatbuf
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

layout(set = 0, binding = 1) uniform writeonly image2D cs_img32;
layout(set = 0, binding = 2) uniform texture2D cs_img36;
layout(set = 0, binding = 3) uniform utexture2D cs_img16;
layout(set = 0, binding = 4) uniform texture2D cs_img24;
layout(set = 0, binding = 5) uniform sampler cs_sampsgpr_49;

shared _53 shared_mem_u32;
shared _59 shared_mem_u64;

void main()
{
    precise float _146 = 0.1902500092983245849609375 * float(gl_LocalInvocationID.x);
    uint _150 = gl_WorkGroupID.y << 3u;
    uint _151 = gl_WorkGroupID.x << 3u;
    precise float _153 = 12.0 * fract(_146);
    uint _155 = _151 + 4294967294u;
    uint _156 = _150 + 4294967294u;
    uint _169 = 21u & (gl_LocalInvocationID.x >> 1u);
    uint _170 = 21u & gl_LocalInvocationID.x;
    uint _176 = 19u & ((_169 >> 1u) | _169);
    uint _177 = 19u & ((_170 >> 1u) | _170);
    uint _184 = 7u & ((_176 >> 2u) | _176);
    uint _185 = 7u & ((_177 >> 2u) | _177);
    uint _186 = _150 | _184;
    uint _187 = _151 | _185;
    uvec4 _190 = subgroupBallot(2147483647u < floatBitsToUint(uintBitsToFloat(texelFetch(cs_img16, ivec2(uvec2(_155 + uint(_146), _156 + uint(_153))), 0)).y));
    uint _191 = _190.x;
    bool _198 = (packUint2x32(uvec2(_191, _190.y)) & packUint2x32(uvec2(_191, _190.y))) != 0ul;
    if (_198)
    {
        uint _201 = 64u | gl_LocalInvocationID.x;
        full_result_u32x2 _203;
        umulExtended(2863311531u, gl_LocalInvocationID.x, _203._m1, _203._m0);
        full_result_u32x2 _205;
        umulExtended(2863311531u, _201, _205._m1, _205._m0);
        uint _207 = _203._m1 >> 3u;
        uint _208 = _205._m1 >> 3u;
        uint _213 = srt_flatbuf_1.data[44u];
        uint _217 = srt_flatbuf_1.data[45u];
        uint _234 = uint(max(int(0u), int(uint(min(int(_213), int(_155 + (gl_LocalInvocationID.x - (bitfieldExtract(_207, int(0u), int(24u)) * 12u))))))));
        uint _235 = uint(max(int(0u), int(uint(min(int(_217), int(_156 + _207))))));
        uint _236 = uint(max(int(0u), int(uint(min(int(_213), int(_155 + (_201 - (bitfieldExtract(_208, int(0u), int(24u)) * 12u))))))));
        uint _237 = uint(max(int(0u), int(uint(min(int(_217), int(_156 + _208))))));
        vec4 _241 = uintBitsToFloat(texelFetch(cs_img16, ivec2(uvec2(_234, _235)), 0));
        vec4 _249 = uintBitsToFloat(texelFetch(cs_img16, ivec2(uvec2(_236, _237)), 0));
        uint _265 = 128u | gl_LocalInvocationID.x;
        shared_mem_u64._m0[(gl_LocalInvocationID.x << 3u) >> 3u] = packUint2x32(uvec2(floatBitsToUint(_241.x), floatBitsToUint(_241.y)));
        shared_mem_u32._m0[((gl_LocalInvocationID.x << 2u) + 1152u) >> 2u] = floatBitsToUint(texelFetch(cs_img24, ivec2(uvec2(_234, _235)), 0).x);
        shared_mem_u64._m0[(_201 << 3u) >> 3u] = packUint2x32(uvec2(floatBitsToUint(_249.x), floatBitsToUint(_249.y)));
        shared_mem_u32._m0[((_201 << 2u) + 1152u) >> 2u] = floatBitsToUint(texelFetch(cs_img24, ivec2(uvec2(_236, _237)), 0).x);
        uvec4 _287 = subgroupBallot(true);
        if (144u > _265)
        {
            full_result_u32x2 _291;
            umulExtended(2863311531u, _265, _291._m1, _291._m0);
            uint _293 = _291._m1 >> 3u;
            uint _301 = uint(max(int(0u), int(uint(min(int(_213), int(_155 + (_265 - (bitfieldExtract(_293, int(0u), int(24u)) * 12u))))))));
            uint _302 = uint(max(int(0u), int(uint(min(int(_217), int(_156 + _293))))));
            vec4 _306 = uintBitsToFloat(texelFetch(cs_img16, ivec2(uvec2(_301, _302)), 0));
            shared_mem_u64._m0[(_265 << 3u) >> 3u] = packUint2x32(uvec2(floatBitsToUint(_306.x), floatBitsToUint(_306.y)));
            shared_mem_u32._m0[((_265 << 2u) + 1152u) >> 2u] = floatBitsToUint(texelFetch(cs_img24, ivec2(uvec2(_301, _302)), 0).x);
        }
        uint _326 = gl_SubgroupInvocationID & 63u;
        bool _334 = ((((_326 >= 32u) ? _287.y : _287.x) >> (_326 & 31u)) & 1u) != 0u;
        uint _339 = (bitfieldExtract(_184 + 2u, int(0u), int(24u)) * 12u) + (_185 + 2u);
        uint _340 = _339 << 2u;
        groupMemoryBarrier();
        uint _344 = (_340 + 1048u) >> 2u;
        uint _348 = (_340 + 1152u) >> 2u;
        uvec2 _355 = unpackUint2x32(shared_mem_u64._m0[(_339 << 3u) >> 3u]);
        uint _356 = _355.x;
        uint _357 = _355.y;
        uvec4 _362 = subgroupBallot(_334);
        uint _363 = _362.x;
        uint _364 = _362.y;
        uint _373;
        uint _374;
        if (_334 && (_334 && (uintBitsToFloat(shared_mem_u32._m0[_344]) > uintBitsToFloat(shared_mem_u32._m0[_348]))))
        {
            _373 = shared_mem_u32._m0[(((_339 << 3u) - 256u) + 52u) >> 2u];
            _374 = shared_mem_u32._m0[_344];
        }
        else
        {
            _373 = _357;
            _374 = shared_mem_u32._m0[_348];
        }
        uint _376 = gl_SubgroupInvocationID & 63u;
        uint _386 = ((_339 << 2u) + 1064u) >> 2u;
        uint _401;
        uint _402;
        if ((((((_376 >= 32u) ? _364 : _363) >> (_376 & 31u)) & 1u) != 0u) && (uintBitsToFloat(shared_mem_u32._m0[_386]) > uintBitsToFloat(_374)))
        {
            _401 = shared_mem_u32._m0[(((_339 << 3u) - 192u) + 20u) >> 2u];
            _402 = shared_mem_u32._m0[_386];
        }
        else
        {
            _401 = _373;
            _402 = _374;
        }
        uint _404 = gl_SubgroupInvocationID & 63u;
        bool _410 = ((((_404 >= 32u) ? _364 : _363) >> (_404 & 31u)) & 1u) != 0u;
        uint _414 = ((_339 << 2u) + 1240u) >> 2u;
        uint _428;
        uint _429;
        if (_410 && (_410 && (uintBitsToFloat(shared_mem_u32._m0[_414]) > uintBitsToFloat(_402))))
        {
            _428 = shared_mem_u32._m0[((_339 << 3u) + 180u) >> 2u];
            _429 = shared_mem_u32._m0[_414];
        }
        else
        {
            _428 = _401;
            _429 = _402;
        }
        uint _447;
        if (_410 && (_410 && (uintBitsToFloat(shared_mem_u32._m0[((_339 << 2u) + 1256u) >> 2u]) > uintBitsToFloat(_429))))
        {
            _447 = shared_mem_u32._m0[((_339 << 3u) + 212u) >> 2u];
        }
        else
        {
            _447 = _428;
        }
        uvec4 _450 = subgroupBallot(_410 && (_217 < _186));
        uint _456 = gl_SubgroupInvocationID & 63u;
        bool _465 = _410 && (!((_410 && (_213 < _187)) || (((((_456 >= 32u) ? _450.y : _450.x) >> (_456 & 31u)) & 1u) != 0u)));
        if (_465)
        {
            precise float _479 = 0.5 + float(_187);
            precise float _480 = 0.5 + float(_186);
            precise float _482 = uintBitsToFloat(srt_flatbuf_1.data[46u]) * _479;
            precise float _484 = uintBitsToFloat(srt_flatbuf_1.data[47u]) * _480;
            uvec4 _485 = subgroupBallot(_465);
            bool _488 = _465 && (_465 && (int(0u) > int(_447)));
            uint _534;
            uint _535;
            if (_488)
            {
                precise float _499 = 0.001956947147846221923828125 * float(bitfieldExtract(_447, int(8u), int(9u)));
                precise float _501 = 0.001956947147846221923828125 * float(bitfieldExtract(_447, int(18u), int(9u)));
                precise float _503 = _499 * _499;
                uint _504 = floatBitsToUint(_503);
                uvec4 _507 = subgroupBallot(_488 && (0u != (512u & (_447 >> 8u))));
                precise float _510 = _501 * _501;
                uint _511 = floatBitsToUint(_510);
                uint _515 = gl_SubgroupInvocationID & 63u;
                precise float _529 = 0.25 * uintBitsToFloat((((((_515 >= 32u) ? _507.y : _507.x) >> (_515 & 31u)) & 1u) != 0u) ? (_504 ^ 2147483648u) : _504);
                precise float _532 = 0.25 * uintBitsToFloat((_488 && (0u != (512u & (_447 >> 18u)))) ? (_511 ^ 2147483648u) : _511);
                _534 = floatBitsToUint(_532);
                _535 = floatBitsToUint(_529);
            }
            else
            {
                _534 = 0u;
                _535 = 0u;
            }
            uint _537 = gl_SubgroupInvocationID & 63u;
            bool _543 = ((((_537 >= 32u) ? _485.y : _485.x) >> (_537 & 31u)) & 1u) != 0u;
            precise float _545 = uintBitsToFloat(_535) + _482;
            precise float _547 = uintBitsToFloat(_534) + _484;
            vec4 _552 = textureLod(sampler2D(cs_img36, cs_sampsgpr_49), vec2(_545, _547), 0.0);
            float _553 = _552.x;
            float _556 = _552.w;
            precise float _563 = 1.0 + (-abs(_553));
            float _566 = 1.0 / max(9.9999997473787516355514526367188e-05, _563);
            precise float _567 = _553 * _566;
            precise float _569 = _552.y * _566;
            precise float _571 = _552.z * _566;
            uvec4 _573 = subgroupBallot(_543);
            uint _599;
            uint _600;
            uint _601;
            uint _602;
            if (_543 && (_543 && (int(0u) > int(_357))))
            {
                uint _584 = (_356 >> 27u) + 4294967272u;
                precise float _597 = 0.0039215688593685626983642578125 * float(bitfieldExtract(_357, int(0u), int(8u)));
                _599 = floatBitsToUint(_597);
                _600 = floatBitsToUint(ldexp(float(bitfieldExtract(_356, int(18u), int(9u))), int(_584)));
                _601 = floatBitsToUint(ldexp(float(511u & _356), int(_584)));
                _602 = floatBitsToUint(ldexp(float(bitfieldExtract(_356, int(9u), int(9u))), int(_584)));
            }
            else
            {
                _599 = 0u;
                _600 = 0u;
                _601 = 0u;
                _602 = 0u;
            }
            uint _604 = gl_SubgroupInvocationID & 63u;
            bool _610 = ((((_604 >= 32u) ? _573.y : _573.x) >> (_604 & 31u)) & 1u) != 0u;
            uint _612 = (_339 << 3u) - 192u;
            uint _613 = _612 >> 2u;
            uint _617 = (_612 + 4u) >> 2u;
            precise float _621 = 0.5 * uintBitsToFloat(_602);
            precise float _624 = uintBitsToFloat(_601) + uintBitsToFloat(_600);
            precise float _628 = 0.5 * uintBitsToFloat(_601);
            precise float _629 = _624 * 0.25;
            precise float _630 = _629 + _621;
            precise float _632 = _624 * (-0.25);
            precise float _633 = _632 + _621;
            precise float _636 = (-0.5) * uintBitsToFloat(_600);
            precise float _637 = _636 + _628;
            uvec4 _638 = subgroupBallot(_610);
            uint _660;
            uint _661;
            uint _662;
            uint _663;
            if (_610 && (_610 && (int(0u) > int(shared_mem_u32._m0[_617]))))
            {
                uint _646 = (shared_mem_u32._m0[_613] >> 27u) + 4294967272u;
                precise float _658 = 0.0039215688593685626983642578125 * float(bitfieldExtract(shared_mem_u32._m0[_617], int(0u), int(8u)));
                _660 = floatBitsToUint(_658);
                _661 = floatBitsToUint(ldexp(float(bitfieldExtract(shared_mem_u32._m0[_613], int(18u), int(9u))), int(_646)));
                _662 = floatBitsToUint(ldexp(float(511u & shared_mem_u32._m0[_613]), int(_646)));
                _663 = floatBitsToUint(ldexp(float(bitfieldExtract(shared_mem_u32._m0[_613], int(9u), int(9u))), int(_646)));
            }
            else
            {
                _660 = 0u;
                _661 = 0u;
                _662 = 0u;
                _663 = 0u;
            }
            uint _665 = gl_SubgroupInvocationID & 63u;
            bool _671 = ((((_665 >= 32u) ? _638.y : _638.x) >> (_665 & 31u)) & 1u) != 0u;
            uint _673 = (_339 << 3u) - 128u;
            uint _675 = (_673 + 24u) >> 2u;
            uint _679 = (_673 + 28u) >> 2u;
            precise float _683 = 0.5 * uintBitsToFloat(_663);
            precise float _686 = uintBitsToFloat(_662) + uintBitsToFloat(_661);
            precise float _688 = 0.5 * uintBitsToFloat(_662);
            precise float _691 = _686 * 0.25;
            precise float _692 = _691 + _683;
            precise float _693 = _686 * (-0.25);
            precise float _694 = _693 + _683;
            precise float _696 = (-0.5) * uintBitsToFloat(_661);
            precise float _697 = _696 + _688;
            precise float _704 = _630 + _692;
            precise float _705 = _637 + _697;
            precise float _706 = _633 + _694;
            uvec4 _713 = subgroupBallot(_671);
            uint _735;
            uint _736;
            uint _737;
            uint _738;
            if (_671 && (_671 && (int(0u) > int(shared_mem_u32._m0[_679]))))
            {
                uint _721 = (shared_mem_u32._m0[_675] >> 27u) + 4294967272u;
                precise float _733 = 0.0039215688593685626983642578125 * float(bitfieldExtract(shared_mem_u32._m0[_679], int(0u), int(8u)));
                _735 = floatBitsToUint(_733);
                _736 = floatBitsToUint(ldexp(float(bitfieldExtract(shared_mem_u32._m0[_675], int(18u), int(9u))), int(_721)));
                _737 = floatBitsToUint(ldexp(float(511u & shared_mem_u32._m0[_675]), int(_721)));
                _738 = floatBitsToUint(ldexp(float(bitfieldExtract(shared_mem_u32._m0[_675], int(9u), int(9u))), int(_721)));
            }
            else
            {
                _735 = 0u;
                _736 = 0u;
                _737 = 0u;
                _738 = 0u;
            }
            uint _740 = gl_SubgroupInvocationID & 63u;
            bool _746 = ((((_740 >= 32u) ? _713.y : _713.x) >> (_740 & 31u)) & 1u) != 0u;
            uint _748 = (_339 << 3u) - 128u;
            uint _750 = (_748 + 32u) >> 2u;
            uint _755 = (_748 + 36u) >> 2u;
            precise float _759 = 0.5 * uintBitsToFloat(_738);
            precise float _762 = uintBitsToFloat(_737) + uintBitsToFloat(_736);
            precise float _764 = 0.5 * uintBitsToFloat(_737);
            precise float _767 = _762 * 0.25;
            precise float _768 = _767 + _759;
            precise float _769 = _762 * (-0.25);
            precise float _770 = _769 + _759;
            precise float _772 = (-0.5) * uintBitsToFloat(_736);
            precise float _773 = _772 + _764;
            precise float _780 = _704 + _768;
            precise float _781 = _705 + _773;
            precise float _782 = _706 + _770;
            uvec4 _787 = subgroupBallot(_746);
            uint _809;
            uint _810;
            uint _811;
            uint _812;
            if (_746 && (_746 && (int(0u) > int(shared_mem_u32._m0[_755]))))
            {
                uint _795 = (shared_mem_u32._m0[_750] >> 27u) + 4294967272u;
                precise float _807 = 0.0039215688593685626983642578125 * float(bitfieldExtract(shared_mem_u32._m0[_755], int(0u), int(8u)));
                _809 = floatBitsToUint(_807);
                _810 = floatBitsToUint(ldexp(float(bitfieldExtract(shared_mem_u32._m0[_750], int(18u), int(9u))), int(_795)));
                _811 = floatBitsToUint(ldexp(float(511u & shared_mem_u32._m0[_750]), int(_795)));
                _812 = floatBitsToUint(ldexp(float(bitfieldExtract(shared_mem_u32._m0[_750], int(9u), int(9u))), int(_795)));
            }
            else
            {
                _809 = 0u;
                _810 = 0u;
                _811 = 0u;
                _812 = 0u;
            }
            uint _814 = gl_SubgroupInvocationID & 63u;
            bool _820 = ((((_814 >= 32u) ? _787.y : _787.x) >> (_814 & 31u)) & 1u) != 0u;
            precise float _822 = 0.5 * uintBitsToFloat(_812);
            precise float _825 = uintBitsToFloat(_811) + uintBitsToFloat(_810);
            precise float _827 = 0.5 * uintBitsToFloat(_811);
            precise float _828 = _825 * 0.25;
            precise float _829 = _828 + _822;
            precise float _830 = _825 * (-0.25);
            precise float _831 = _830 + _822;
            uint _833 = (_339 << 3u) - 128u;
            uint _836 = (_833 + 40u) >> 2u;
            uint _840 = (_833 + 44u) >> 2u;
            precise float _844 = (-0.5) * uintBitsToFloat(_810);
            precise float _845 = _844 + _827;
            precise float _850 = _780 + _829;
            precise float _852 = _781 + _845;
            precise float _854 = _782 + _831;
            uvec4 _863 = subgroupBallot(_820);
            uint _885;
            uint _886;
            uint _887;
            uint _888;
            if (_820 && (_820 && (int(0u) > int(shared_mem_u32._m0[_840]))))
            {
                precise float _874 = 0.0039215688593685626983642578125 * float(bitfieldExtract(shared_mem_u32._m0[_840], int(0u), int(8u)));
                uint _877 = (shared_mem_u32._m0[_836] >> 27u) + 4294967272u;
                _885 = floatBitsToUint(_874);
                _886 = floatBitsToUint(ldexp(float(bitfieldExtract(shared_mem_u32._m0[_836], int(18u), int(9u))), int(_877)));
                _887 = floatBitsToUint(ldexp(float(511u & shared_mem_u32._m0[_836]), int(_877)));
                _888 = floatBitsToUint(ldexp(float(bitfieldExtract(shared_mem_u32._m0[_836], int(9u), int(9u))), int(_877)));
            }
            else
            {
                _885 = 0u;
                _886 = 0u;
                _887 = 0u;
                _888 = 0u;
            }
            uint _890 = gl_SubgroupInvocationID & 63u;
            bool _896 = ((((_890 >= 32u) ? _863.y : _863.x) >> (_890 & 31u)) & 1u) != 0u;
            precise float _898 = 0.5 * uintBitsToFloat(_888);
            precise float _901 = uintBitsToFloat(_887) + uintBitsToFloat(_886);
            precise float _902 = _901 * 0.25;
            precise float _903 = _902 + _898;
            precise float _904 = _901 * (-0.25);
            precise float _905 = _904 + _898;
            precise float _908 = _850 + _903;
            precise float _909 = _854 + _905;
            precise float _915 = 0.5 * uintBitsToFloat(_887);
            precise float _917 = (-0.5) * uintBitsToFloat(_886);
            precise float _918 = _917 + _915;
            precise float _922 = _852 + _918;
            uint _925 = (_339 << 3u) - 64u;
            uint _928 = (_925 + 48u) >> 2u;
            uint _932 = (_925 + 52u) >> 2u;
            uvec4 _937 = subgroupBallot(_896);
            uint _959;
            uint _960;
            uint _961;
            uint _962;
            if (_896 && (_896 && (int(0u) > int(shared_mem_u32._m0[_932]))))
            {
                uint _948 = (shared_mem_u32._m0[_928] >> 27u) + 4294967272u;
                precise float _957 = 0.0039215688593685626983642578125 * float(bitfieldExtract(shared_mem_u32._m0[_932], int(0u), int(8u)));
                _959 = floatBitsToUint(_957);
                _960 = floatBitsToUint(ldexp(float(bitfieldExtract(shared_mem_u32._m0[_928], int(18u), int(9u))), int(_948)));
                _961 = floatBitsToUint(ldexp(float(511u & shared_mem_u32._m0[_928]), int(_948)));
                _962 = floatBitsToUint(ldexp(float(bitfieldExtract(shared_mem_u32._m0[_928], int(9u), int(9u))), int(_948)));
            }
            else
            {
                _959 = 0u;
                _960 = 0u;
                _961 = 0u;
                _962 = 0u;
            }
            uint _964 = gl_SubgroupInvocationID & 63u;
            bool _970 = ((((_964 >= 32u) ? _937.y : _937.x) >> (_964 & 31u)) & 1u) != 0u;
            precise float _972 = 0.5 * uintBitsToFloat(_962);
            precise float _975 = uintBitsToFloat(_961) + uintBitsToFloat(_960);
            precise float _979 = 0.5 * uintBitsToFloat(_961);
            precise float _981 = (-0.5) * uintBitsToFloat(_960);
            precise float _982 = _981 + _979;
            precise float _985 = _922 + _982;
            precise float _986 = _975 * 0.25;
            precise float _987 = _986 + _972;
            precise float _988 = _975 * (-0.25);
            precise float _989 = _988 + _972;
            precise float _992 = _908 + _987;
            precise float _997 = _909 + _989;
            uint _999 = (_339 << 3u) - 64u;
            uint _1002 = (_999 + 56u) >> 2u;
            uint _1007 = (_999 + 60u) >> 2u;
            uvec4 _1012 = subgroupBallot(_970);
            uint _1034;
            uint _1035;
            uint _1036;
            uint _1037;
            if (_970 && (_970 && (int(0u) > int(shared_mem_u32._m0[_1007]))))
            {
                precise float _1023 = 0.0039215688593685626983642578125 * float(bitfieldExtract(shared_mem_u32._m0[_1007], int(0u), int(8u)));
                uint _1026 = (shared_mem_u32._m0[_1002] >> 27u) + 4294967272u;
                _1034 = floatBitsToUint(_1023);
                _1035 = floatBitsToUint(ldexp(float(bitfieldExtract(shared_mem_u32._m0[_1002], int(18u), int(9u))), int(_1026)));
                _1036 = floatBitsToUint(ldexp(float(bitfieldExtract(shared_mem_u32._m0[_1002], int(9u), int(9u))), int(_1026)));
                _1037 = floatBitsToUint(ldexp(float(511u & shared_mem_u32._m0[_1002]), int(_1026)));
            }
            else
            {
                _1034 = 0u;
                _1035 = 0u;
                _1036 = 0u;
                _1037 = 0u;
            }
            uint _1039 = gl_SubgroupInvocationID & 63u;
            bool _1045 = ((((_1039 >= 32u) ? _1012.y : _1012.x) >> (_1039 & 31u)) & 1u) != 0u;
            precise float _1047 = 0.5 * uintBitsToFloat(_1037);
            precise float _1049 = 0.5 * uintBitsToFloat(_1036);
            precise float _1052 = uintBitsToFloat(_1037) + uintBitsToFloat(_1035);
            precise float _1054 = (-0.5) * uintBitsToFloat(_1035);
            precise float _1055 = _1054 + _1047;
            precise float _1056 = _1052 * 0.25;
            precise float _1057 = _1056 + _1049;
            precise float _1058 = _1052 * (-0.25);
            precise float _1059 = _1058 + _1049;
            precise float _1061 = _985 + _1055;
            precise float _1065 = _992 + _1057;
            precise float _1073 = _997 + _1059;
            uvec2 _1078 = unpackUint2x32(shared_mem_u64._m0[((_339 << 3u) + 8u) >> 3u]);
            uint _1079 = _1078.x;
            uint _1080 = _1078.y;
            uvec4 _1083 = subgroupBallot(_1045);
            uint _1105;
            uint _1106;
            uint _1107;
            uint _1108;
            if (_1045 && (_1045 && (int(0u) > int(_1080))))
            {
                precise float _1093 = 0.0039215688593685626983642578125 * float(bitfieldExtract(_1080, int(0u), int(8u)));
                uint _1096 = (_1079 >> 27u) + 4294967272u;
                _1105 = floatBitsToUint(_1093);
                _1106 = floatBitsToUint(ldexp(float(bitfieldExtract(_1079, int(18u), int(9u))), int(_1096)));
                _1107 = floatBitsToUint(ldexp(float(511u & _1079), int(_1096)));
                _1108 = floatBitsToUint(ldexp(float(bitfieldExtract(_1079, int(9u), int(9u))), int(_1096)));
            }
            else
            {
                _1105 = 0u;
                _1106 = 0u;
                _1107 = 0u;
                _1108 = 0u;
            }
            uint _1110 = gl_SubgroupInvocationID & 63u;
            bool _1116 = ((((_1110 >= 32u) ? _1083.y : _1083.x) >> (_1110 & 31u)) & 1u) != 0u;
            precise float _1118 = 0.5 * uintBitsToFloat(_1108);
            precise float _1121 = uintBitsToFloat(_1107) + uintBitsToFloat(_1106);
            precise float _1122 = _1121 * 0.25;
            precise float _1123 = _1122 + _1118;
            precise float _1124 = _1121 * (-0.25);
            precise float _1125 = _1124 + _1118;
            precise float _1129 = _1065 + _1123;
            precise float _1132 = _1073 + _1125;
            precise float _1136 = 0.5 * uintBitsToFloat(_1107);
            precise float _1138 = (-0.5) * uintBitsToFloat(_1106);
            precise float _1139 = _1138 + _1136;
            uvec2 _1149 = unpackUint2x32(shared_mem_u64._m0[((_339 << 3u) + 16u) >> 3u]);
            uint _1150 = _1149.x;
            uint _1151 = _1149.y;
            precise float _1152 = _1061 + _1139;
            uvec4 _1155 = subgroupBallot(_1116);
            uint _1177;
            uint _1178;
            uint _1179;
            uint _1180;
            if (_1116 && (_1116 && (int(0u) > int(_1151))))
            {
                precise float _1165 = 0.0039215688593685626983642578125 * float(bitfieldExtract(_1151, int(0u), int(8u)));
                uint _1168 = (_1150 >> 27u) + 4294967272u;
                _1177 = floatBitsToUint(_1165);
                _1178 = floatBitsToUint(ldexp(float(bitfieldExtract(_1150, int(18u), int(9u))), int(_1168)));
                _1179 = floatBitsToUint(ldexp(float(511u & _1150), int(_1168)));
                _1180 = floatBitsToUint(ldexp(float(bitfieldExtract(_1150, int(9u), int(9u))), int(_1168)));
            }
            else
            {
                _1177 = 0u;
                _1178 = 0u;
                _1179 = 0u;
                _1180 = 0u;
            }
            uint _1182 = gl_SubgroupInvocationID & 63u;
            bool _1188 = ((((_1182 >= 32u) ? _1155.y : _1155.x) >> (_1182 & 31u)) & 1u) != 0u;
            precise float _1190 = 0.5 * uintBitsToFloat(_1180);
            precise float _1193 = uintBitsToFloat(_1179) + uintBitsToFloat(_1178);
            precise float _1195 = 0.5 * uintBitsToFloat(_1179);
            precise float _1197 = (-0.5) * uintBitsToFloat(_1178);
            precise float _1198 = _1197 + _1195;
            precise float _1203 = _1152 + _1198;
            precise float _1206 = _1193 * 0.25;
            precise float _1207 = _1206 + _1190;
            precise float _1208 = _1193 * (-0.25);
            precise float _1209 = _1208 + _1190;
            precise float _1213 = _1129 + _1207;
            precise float _1215 = _1132 + _1209;
            uvec2 _1222 = unpackUint2x32(shared_mem_u64._m0[((_339 << 3u) + 88u) >> 3u]);
            uint _1223 = _1222.x;
            uint _1224 = _1222.y;
            uvec4 _1227 = subgroupBallot(_1188);
            uint _1249;
            uint _1250;
            uint _1251;
            uint _1252;
            if (_1188 && (_1188 && (int(0u) > int(_1224))))
            {
                uint _1239 = (_1223 >> 27u) + 4294967272u;
                precise float _1247 = 0.0039215688593685626983642578125 * float(bitfieldExtract(_1224, int(0u), int(8u)));
                _1249 = floatBitsToUint(_1247);
                _1250 = floatBitsToUint(ldexp(float(bitfieldExtract(_1223, int(18u), int(9u))), int(_1239)));
                _1251 = floatBitsToUint(ldexp(float(511u & _1223), int(_1239)));
                _1252 = floatBitsToUint(ldexp(float(bitfieldExtract(_1223, int(9u), int(9u))), int(_1239)));
            }
            else
            {
                _1249 = 0u;
                _1250 = 0u;
                _1251 = 0u;
                _1252 = 0u;
            }
            uint _1254 = gl_SubgroupInvocationID & 63u;
            bool _1260 = ((((_1254 >= 32u) ? _1227.y : _1227.x) >> (_1254 & 31u)) & 1u) != 0u;
            precise float _1262 = 0.5 * uintBitsToFloat(_1252);
            precise float _1265 = uintBitsToFloat(_1251) + uintBitsToFloat(_1250);
            precise float _1267 = 0.5 * uintBitsToFloat(_1251);
            precise float _1269 = (-0.5) * uintBitsToFloat(_1250);
            precise float _1270 = _1269 + _1267;
            precise float _1271 = _1203 + _1270;
            precise float _1278 = _1265 * 0.25;
            precise float _1279 = _1278 + _1262;
            precise float _1280 = _1265 * (-0.25);
            precise float _1281 = _1280 + _1262;
            precise float _1286 = _1213 + _1279;
            precise float _1287 = _1215 + _1281;
            uvec2 _1294 = unpackUint2x32(shared_mem_u64._m0[((_339 << 3u) + 96u) >> 3u]);
            uint _1295 = _1294.x;
            uint _1296 = _1294.y;
            uvec4 _1299 = subgroupBallot(_1260);
            uint _1321;
            uint _1322;
            uint _1323;
            uint _1324;
            if (_1260 && (_1260 && (int(0u) > int(_1296))))
            {
                uint _1310 = (_1295 >> 27u) + 4294967272u;
                precise float _1319 = 0.0039215688593685626983642578125 * float(bitfieldExtract(_1296, int(0u), int(8u)));
                _1321 = floatBitsToUint(_1319);
                _1322 = floatBitsToUint(ldexp(float(bitfieldExtract(_1295, int(18u), int(9u))), int(_1310)));
                _1323 = floatBitsToUint(ldexp(float(511u & _1295), int(_1310)));
                _1324 = floatBitsToUint(ldexp(float(bitfieldExtract(_1295, int(9u), int(9u))), int(_1310)));
            }
            else
            {
                _1321 = 0u;
                _1322 = 0u;
                _1323 = 0u;
                _1324 = 0u;
            }
            uint _1326 = gl_SubgroupInvocationID & 63u;
            bool _1332 = ((((_1326 >= 32u) ? _1299.y : _1299.x) >> (_1326 & 31u)) & 1u) != 0u;
            precise float _1334 = 0.5 * uintBitsToFloat(_1324);
            precise float _1337 = uintBitsToFloat(_1323) + uintBitsToFloat(_1322);
            precise float _1338 = _1337 * 0.25;
            precise float _1339 = _1338 + _1334;
            precise float _1340 = _1337 * (-0.25);
            precise float _1341 = _1340 + _1334;
            float _1343 = min(uintBitsToFloat(_1321), min(uintBitsToFloat(_1105), min(uintBitsToFloat(_1034), min(uintBitsToFloat(_599), uintBitsToFloat(_809)))));
            precise float _1345 = 0.5 * uintBitsToFloat(_1323);
            precise float _1347 = (-0.5) * uintBitsToFloat(_1322);
            precise float _1348 = _1347 + _1345;
            precise float _1349 = _1287 + _1341;
            float _1350 = min(min(min(min(_633, _831), _1059), _1125), _1341);
            precise float _1351 = _1271 + _1348;
            float _1352 = max(max(max(max(_630, _829), _1057), _1123), _1339);
            float _1354 = max(uintBitsToFloat(_1321), max(uintBitsToFloat(_1105), max(uintBitsToFloat(_1034), max(uintBitsToFloat(_599), uintBitsToFloat(_809)))));
            float _1355 = min(min(min(min(_637, _845), _1055), _1139), _1348);
            float _1356 = max(max(max(max(_637, _845), _1055), _1139), _1348);
            float _1357 = max(max(max(max(_633, _831), _1059), _1125), _1341);
            precise float _1358 = _1286 + _1339;
            float _1359 = min(min(min(min(_630, _829), _1057), _1123), _1339);
            uvec2 _1366 = unpackUint2x32(shared_mem_u64._m0[((_339 << 3u) + 104u) >> 3u]);
            uint _1367 = _1366.x;
            uint _1368 = _1366.y;
            uvec4 _1371 = subgroupBallot(_1332);
            uint _1393;
            uint _1394;
            uint _1395;
            uint _1396;
            if (_1332 && (_1332 && (int(0u) > int(_1368))))
            {
                precise float _1382 = 0.0039215688593685626983642578125 * float(bitfieldExtract(_1368, int(0u), int(8u)));
                uint _1385 = (_1367 >> 27u) + 4294967272u;
                _1393 = floatBitsToUint(ldexp(float(bitfieldExtract(_1367, int(18u), int(9u))), int(_1385)));
                _1394 = floatBitsToUint(ldexp(float(511u & _1367), int(_1385)));
                _1395 = floatBitsToUint(_1382);
                _1396 = floatBitsToUint(ldexp(float(bitfieldExtract(_1367, int(9u), int(9u))), int(_1385)));
            }
            else
            {
                _1393 = 0u;
                _1394 = 0u;
                _1395 = 0u;
                _1396 = 0u;
            }
            uint _1398 = gl_SubgroupInvocationID & 63u;
            bool _1404 = ((((_1398 >= 32u) ? _1371.y : _1371.x) >> (_1398 & 31u)) & 1u) != 0u;
            precise float _1406 = 0.5 * uintBitsToFloat(_1396);
            precise float _1412 = uintBitsToFloat(_1394) + uintBitsToFloat(_1393);
            precise float _1413 = _1412 * 0.25;
            precise float _1414 = _1413 + _1406;
            precise float _1415 = _1412 * (-0.25);
            precise float _1416 = _1415 + _1406;
            precise float _1421 = 0.5 * uintBitsToFloat(_1394);
            precise float _1423 = (-0.5) * uintBitsToFloat(_1393);
            precise float _1424 = _1423 + _1421;
            precise float _1429 = _1351 + _1424;
            precise float _1431 = _1358 + _1414;
            uvec2 _1436 = unpackUint2x32(shared_mem_u64._m0[((_339 << 3u) + 192u) >> 3u]);
            uint _1437 = _1436.x;
            uint _1438 = _1436.y;
            precise float _1439 = _1349 + _1416;
            uvec4 _1442 = subgroupBallot(_1404);
            uint _1464;
            uint _1465;
            uint _1466;
            uint _1467;
            if (_1404 && (_1404 && (int(0u) > int(_1438))))
            {
                precise float _1453 = 0.0039215688593685626983642578125 * float(bitfieldExtract(_1438, int(0u), int(8u)));
                uint _1456 = (_1437 >> 27u) + 4294967272u;
                _1464 = floatBitsToUint(ldexp(float(bitfieldExtract(_1437, int(18u), int(9u))), int(_1456)));
                _1465 = floatBitsToUint(ldexp(float(511u & _1437), int(_1456)));
                _1466 = floatBitsToUint(ldexp(float(bitfieldExtract(_1437, int(9u), int(9u))), int(_1456)));
                _1467 = floatBitsToUint(_1453);
            }
            else
            {
                _1464 = 0u;
                _1465 = 0u;
                _1466 = 0u;
                _1467 = 0u;
            }
            uint _1469 = gl_SubgroupInvocationID & 63u;
            bool _1475 = ((((_1469 >= 32u) ? _1442.y : _1442.x) >> (_1469 & 31u)) & 1u) != 0u;
            uvec4 _1483 = subgroupBallot(_1475 && (1.0 > _547));
            precise float _1491 = 0.5 * uintBitsToFloat(_1466);
            precise float _1492 = max3(max(uintBitsToFloat(_1395), max(uintBitsToFloat(_1249), max(uintBitsToFloat(_1177), max(uintBitsToFloat(_959), max(uintBitsToFloat(_885), max(uintBitsToFloat(_735), max(uintBitsToFloat(_599), uintBitsToFloat(_660)))))))), uintBitsToFloat(_1467), _1354) - _1354;
            precise float _1497 = uintBitsToFloat(_1465) + uintBitsToFloat(_1464);
            uint _1498 = (_1475 && (!(isnan(_567) || isinf(_567)))) ? floatBitsToUint(_567) : 0u;
            precise float _1500 = 0.5 * uintBitsToFloat(_1465);
            precise float _1502 = (-0.5) * uintBitsToFloat(_1464);
            precise float _1503 = _1502 + _1500;
            precise float _1506 = _1429 + _1503;
            precise float _1507 = max3(_1503, _1356, max(max(max(max(max(max(max(_637, _697), _773), _918), _982), _1198), _1270), _1424)) - _1356;
            precise float _1508 = 0.5 * _1507;
            precise float _1509 = _1508 + _1356;
            precise float _1511 = _1497 * 0.25;
            precise float _1512 = _1511 + _1491;
            precise float _1514 = max3(_1512, _1352, max(max(max(max(max(max(max(_630, _692), _768), _903), _987), _1207), _1279), _1414)) - _1352;
            precise float _1515 = _1431 + _1512;
            precise float _1517 = 0.5 * _1514;
            precise float _1518 = _1517 + _1352;
            precise float _1521 = 0.076923079788684844970703125 * _1515;
            precise float _1522 = min3(_1512, _1359, min(min(min(min(min(min(min(_630, _692), _768), _903), _987), _1207), _1279), _1414)) - _1359;
            precise float _1524 = 0.5 * _1522;
            precise float _1525 = _1524 + _1359;
            precise float _1529 = max(_1525, min(_1518, _1521)) - uintBitsToFloat(_1498);
            precise float _1535 = 0.076923079788684844970703125 * _1506;
            precise float _1536 = _1497 * (-0.25);
            precise float _1537 = _1536 + _1491;
            precise float _1539 = max3(_1537, _1357, max(max(max(max(max(max(max(_633, _694), _770), _905), _989), _1209), _1281), _1416)) - _1357;
            precise float _1540 = min3(_1503, _1355, min(min(min(min(min(min(min(_637, _697), _773), _918), _982), _1198), _1270), _1424)) - _1355;
            precise float _1541 = 0.5 * _1540;
            precise float _1542 = _1541 + _1355;
            precise float _1547 = min3(_1537, _1350, min(min(min(min(min(min(min(_633, _694), _770), _905), _989), _1209), _1281), _1416)) - _1350;
            precise float _1548 = 0.5 * _1539;
            precise float _1549 = _1548 + _1357;
            uint _1553 = (2147483648u & floatBitsToUint(_1529)) | (2147483647u & floatBitsToUint(max(0.001000000047497451305389404296875, abs(_1529))));
            precise float _1559 = 0.5 * _1547;
            precise float _1560 = _1559 + _1350;
            precise float _1562 = _1439 + _1537;
            precise float _1563 = 0.076923079788684844970703125 * _1562;
            uint _1572 = (_1475 && (!(isnan(_569) || isinf(_569)))) ? floatBitsToUint(_569) : 0u;
            precise float _1574 = max(_1542, min(_1509, _1535)) - uintBitsToFloat(_1572);
            uint _1581 = (2147483648u & floatBitsToUint(_1574)) | (2147483647u & floatBitsToUint(max(0.001000000047497451305389404296875, abs(_1574))));
            precise float _1593 = uintBitsToFloat((_1475 && (0.0 < uintBitsToFloat(_1581))) ? floatBitsToUint(_1542) : floatBitsToUint(_1509)) - uintBitsToFloat(_1572);
            precise float _1596 = uintBitsToFloat((_1475 && (0.0 < uintBitsToFloat(_1553))) ? floatBitsToUint(_1525) : floatBitsToUint(_1518)) - uintBitsToFloat(_1498);
            precise float _1599 = (1.0 / uintBitsToFloat(_1553)) * _1596;
            uint _1600 = (_1475 && (!(isnan(_571) || isinf(_571)))) ? floatBitsToUint(_571) : 0u;
            precise float _1601 = (1.0 / uintBitsToFloat(_1581)) * _1593;
            precise float _1603 = max(_1560, min(_1549, _1563)) - uintBitsToFloat(_1600);
            uint _1610 = (2147483648u & floatBitsToUint(_1603)) | (2147483647u & floatBitsToUint(max(0.001000000047497451305389404296875, abs(_1603))));
            uvec4 _1617 = subgroupBallot(_1475 && (0.0 < min(_545, _547)));
            precise float _1624 = uintBitsToFloat((_1475 && (0.0 < uintBitsToFloat(_1610))) ? floatBitsToUint(_1560) : floatBitsToUint(_1549)) - uintBitsToFloat(_1600);
            precise float _1627 = (1.0 / uintBitsToFloat(_1610)) * _1624;
            float _1629 = clamp(max3(_1627, _1599, _1601), 0.0, 1.0);
            uint _1631 = gl_SubgroupInvocationID & 63u;
            uint _1640 = gl_SubgroupInvocationID & 63u;
            precise float _1652 = 1.0 + abs(_630);
            precise float _1653 = min3(min(uintBitsToFloat(_1395), min(uintBitsToFloat(_1249), min(uintBitsToFloat(_1177), min(uintBitsToFloat(_959), min(uintBitsToFloat(_885), min(uintBitsToFloat(_735), min(uintBitsToFloat(_599), uintBitsToFloat(_660)))))))), uintBitsToFloat(_1467), _1343) - _1343;
            precise float _1655 = _1629 * _1529;
            precise float _1656 = _1655 + uintBitsToFloat(_1498);
            precise float _1657 = 0.5 * _1492;
            precise float _1658 = _1657 + _1354;
            float _1659 = 1.0 / _1652;
            precise float _1660 = 0.5 * _1653;
            precise float _1661 = _1660 + _1343;
            precise float _1662 = _1659 * _630;
            precise float _1663 = _1659 * _633;
            precise float _1665 = 1.0 + abs(_1656);
            precise float _1666 = _1659 * _637;
            precise float _1668 = _1629 * _1603;
            precise float _1669 = _1668 + uintBitsToFloat(_1600);
            float _1670 = 1.0 / _1665;
            precise float _1672 = _1629 * _1574;
            precise float _1673 = _1672 + uintBitsToFloat(_1572);
            precise float _1675 = _1670 * _1656;
            precise float _1676 = _1675 + (-_1662);
            uint _1677 = (((((((_1631 >= 32u) ? _1617.y : _1617.x) >> (_1631 & 31u)) & 1u) != 0u) && (_1475 && (1.0 > _545))) && (((((_1640 >= 32u) ? _1483.y : _1483.x) >> (_1640 & 31u)) & 1u) != 0u)) ? srt_flatbuf_1.data[48u] : 0u;
            precise float _1688 = _1670 * _1669;
            precise float _1689 = _1688 + (-_1663);
            precise float _1691 = _1670 * _1673;
            precise float _1692 = _1691 + (-_1666);
            precise float _1694 = max(_1661, min(uintBitsToFloat((_1475 && (!(isnan(_556) || isinf(_556)))) ? floatBitsToUint(_556) : 0u), _1658)) - uintBitsToFloat(_599);
            precise float _1696 = uintBitsToFloat(_1677) * _1676;
            precise float _1697 = _1696 + _1662;
            precise float _1699 = uintBitsToFloat(_1677) * _1692;
            precise float _1700 = _1699 + _1666;
            precise float _1702 = uintBitsToFloat(_1677) * _1689;
            precise float _1703 = _1702 + _1663;
            precise float _1706 = uintBitsToFloat(_1677) * _1694;
            precise float _1707 = _1706 + uintBitsToFloat(_599);
            vec4 _1708 = vec4(_1697, _1700, _1703, _1707);
            imageStore(cs_img32, ivec2(uvec2(_187, _186)), vec4(_1708.x, _1708.y, _1708.z, _1708.w));
        }
    }
    if (!_198)
    {
        imageStore(cs_img32, ivec2(uvec2(_187, _186)), vec4(vec4(0.0).x, vec4(0.0).y, vec4(0.0).z, vec4(0.0).w));
    }
}

