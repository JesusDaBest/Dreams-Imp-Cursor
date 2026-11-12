// CPU frame preparation only: original pixels and interpolation arithmetic.
#include <immintrin.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>
#include <array>

static __m128i rounded_positive(__m128 x) {
    const auto integer = _mm_cvttps_epi32(x);
    const auto fraction = _mm_sub_ps(x, _mm_cvtepi32_ps(integer));
    return _mm_add_epi32(integer, _mm_and_si128(_mm_castps_si128(
        _mm_cmpge_ps(fraction, _mm_set1_ps(.5f))), _mm_set1_epi32(1)));
}
static __m128i display(__m128 linear) {
    const auto x = _mm_max_ps(_mm_setzero_ps(), _mm_sub_ps(linear,_mm_set1_ps(.004f)));
    const auto numerator = _mm_mul_ps(_mm_mul_ps(_mm_set1_ps(255.f),x),
        _mm_fmadd_ps(_mm_set1_ps(6.2f),x,_mm_set1_ps(.5f)));
    const auto denominator = _mm_fmadd_ps(x,
        _mm_fmadd_ps(_mm_set1_ps(6.2f),x,_mm_set1_ps(1.7f)),_mm_set1_ps(.06f));
    return rounded_positive(_mm_div_ps(numerator,denominator));
}
extern "C" __declspec(dllexport) void imp_decode_bgra(
    const uint16_t* source,uint8_t* destination,unsigned count) {
    const auto zero=_mm_setzero_ps(),one=_mm_set1_ps(1.f);
    const auto signless=_mm_castsi128_ps(_mm_set1_epi32(0x7fffffff));
    const auto finite=_mm_set1_ps(65504.f);
    unsigned i=0;
    for(;i+4<=count;i+=4,source+=16,destination+=16) {
        auto y=_mm_cvtph_ps(_mm_loadl_epi64(reinterpret_cast<const __m128i*>(source)));
        auto co=_mm_cvtph_ps(_mm_loadl_epi64(reinterpret_cast<const __m128i*>(source+4)));
        auto cg=_mm_cvtph_ps(_mm_loadl_epi64(reinterpret_cast<const __m128i*>(source+8)));
        auto a=_mm_cvtph_ps(_mm_loadl_epi64(reinterpret_cast<const __m128i*>(source+12)));
        _MM_TRANSPOSE4_PS(y,co,cg,a);
        auto valid=_mm_and_ps(_mm_cmpgt_ps(a,zero),_mm_cmple_ps(a,finite));
        valid=_mm_and_ps(valid,_mm_cmple_ps(_mm_and_ps(y,signless),finite));
        valid=_mm_and_ps(valid,_mm_cmple_ps(_mm_and_ps(co,signless),finite));
        valid=_mm_and_ps(valid,_mm_cmple_ps(_mm_and_ps(cg,signless),finite));
        if(!_mm_movemask_ps(valid)) {
            _mm_storeu_si128(reinterpret_cast<__m128i*>(destination),_mm_setzero_si128());
            continue;
        }
        y=_mm_and_ps(y,valid);co=_mm_and_ps(co,valid);cg=_mm_and_ps(cg,valid);a=_mm_and_ps(a,valid);
        const auto scale=_mm_div_ps(one,_mm_max_ps(_mm_sub_ps(one,_mm_and_ps(y,signless)),_mm_set1_ps(.0001f)));
        auto b=display(_mm_mul_ps(_mm_sub_ps(_mm_sub_ps(y,co),cg),scale));
        auto g=display(_mm_mul_ps(_mm_add_ps(y,cg),scale));
        auto r=display(_mm_mul_ps(_mm_sub_ps(_mm_add_ps(y,co),cg),scale));
        auto alpha=rounded_positive(_mm_mul_ps(_mm_set1_ps(255.f),_mm_min_ps(a,one)));
        const auto mask=_mm_castps_si128(valid);
        b=_mm_and_si128(b,mask);g=_mm_and_si128(g,mask);r=_mm_and_si128(r,mask);
        alpha=_mm_and_si128(_mm_max_epi32(_mm_max_epi32(b,g),_mm_max_epi32(r,alpha)),mask);
        // The previous scalar routine stores uint8_t, preserving its byte conversion.
        const auto low=_mm_set1_epi32(255);
        const auto packed=_mm_or_si128(_mm_or_si128(_mm_and_si128(b,low),_mm_slli_epi32(_mm_and_si128(g,low),8)),
            _mm_or_si128(_mm_slli_epi32(_mm_and_si128(r,low),16),_mm_slli_epi32(_mm_and_si128(alpha,low),24)));
        _mm_storeu_si128(reinterpret_cast<__m128i*>(destination),packed);
    }
    auto scalar=[](float value) {
        const float x=std::max(0.f,value-.004f);
        return uint8_t(std::lround(255.f*x*std::fma(6.2f,x,.5f)/std::fma(x,std::fma(6.2f,x,1.7f),.06f)));
    };
    for(;i<count;++i,source+=4,destination+=4) {
        const float a=_cvtsh_ss(source[3]),y=_cvtsh_ss(source[0]),co=_cvtsh_ss(source[1]),cg=_cvtsh_ss(source[2]);
        if(!(a>0.f)||!std::isfinite(a)||!std::isfinite(y)||!std::isfinite(co)||!std::isfinite(cg)) {
            std::memset(destination,0,4);continue;
        }
        const float scale=1.f/std::max(1.f-std::abs(y),.0001f);
        destination[0]=scalar((y-co-cg)*scale);destination[1]=scalar((y+cg)*scale);destination[2]=scalar((y+co-cg)*scale);
        destination[3]=std::max({destination[0],destination[1],destination[2],uint8_t(std::lround(255.f*std::min(a,1.f)))});
    }
}

// Python computes these expressions in double precision without contraction,
// then packs only the surface values to float. Points remain doubles.
static double interpolate(float a,float b,double amount) {
    volatile double product=(double(b)-double(a))*amount;
    return double(a)+product;
}
extern "C" __declspec(dllexport) void imp_interpolate_samples(
    const uint8_t* previous,const uint8_t* current,uint8_t* destination,
    unsigned state_bytes,unsigned surface_offset,unsigned surface_count,
    unsigned point_offset,unsigned point_stride,unsigned point_count,double amount,double* points,const uint8_t* base) {
    // Retain the latest non-surface state, even between fixed solver ticks.
    std::memcpy(destination,base,state_bytes);
    const auto* a=reinterpret_cast<const float*>(previous+surface_offset);
    const auto* b=reinterpret_cast<const float*>(current+surface_offset);
    auto* out=reinterpret_cast<float*>(destination+surface_offset);
    for(unsigned i=0;i<surface_count;++i)out[i]=static_cast<float>(interpolate(a[i],b[i],amount));
    for(unsigned i=0;i<point_count;++i) {
        const auto* pa=reinterpret_cast<const float*>(previous+point_offset+i*point_stride);
        const auto* pb=reinterpret_cast<const float*>(current+point_offset+i*point_stride);
        for(unsigned axis=0;axis<3;++axis)points[i*3+axis]=interpolate(pa[axis],pb[axis],amount);
    }
}

// Pillow 12.3 bilinear's separable 22-bit coefficients and rounding, with
// four channels evaluated together. Channel swapping commutes with filtering.
struct Axis {
    int input=0,output=0,stride=0;
    std::vector<int> starts,counts,weights;
    void prepare(int in,int out) {
        if(input==in && output==out)return;
        input=in;output=out;
        double scale=double(in)/out, fs=std::max(scale,1.0);
        stride=int(std::ceil(fs))*2+1;
        starts.resize(out);counts.resize(out);weights.assign(size_t(out)*stride,0);
        std::vector<double> values(stride);
        const double inverse=1.0/fs;
        for(int x=0;x<out;++x) {
            const double center=(x+.5)*scale;
            int start=std::max(0,int(center-fs+.5));
            int end=std::min(in,int(center+fs+.5));
            starts[x]=start;counts[x]=end-start;double sum=0;
            for(int i=0;i<end-start;++i) {
                double d=std::abs((i+start-center+.5)*inverse);
                values[i]=d<1.0?1.0-d:0.0;sum+=values[i];
            }
            for(int i=0;i<end-start;++i)
                weights[size_t(x)*stride+i]=int(.5+(sum?values[i]/sum:values[i])*(1<<22));
        }
    }
};
static uint32_t pack_filtered(__m128i sum) {
    sum=_mm_srai_epi32(sum,22);
    sum=_mm_packus_epi32(sum,sum);sum=_mm_packus_epi16(sum,sum);
    return uint32_t(_mm_cvtsi128_si32(sum));
}
extern "C" __declspec(dllexport) int imp_resize_rgba(
    const uint8_t* bgra,int sw,int sh,uint8_t* rgba,int dw,int dh) {
    if(!bgra || !rgba || sw<=0 || sh<=0 || dw<=0 || dh<=0 ||
       sw>4096 || sh>4096 || dw>4096 || dh>4096)return 0;
    try {
        struct Cache {Axis x,y;std::vector<uint8_t> temporary;};
        // Two alternating sizes cover the carousel thumbnails and hero.
        static thread_local std::array<Cache,2> caches;
        static thread_local unsigned next=0;
        Cache* chosen=nullptr;
        for(auto& c:caches)if(c.x.input==sw&&c.x.output==dw&&c.y.input==sh&&c.y.output==dh)chosen=&c;
        if(!chosen)chosen=&caches[(next++)%caches.size()];
        auto& c=*chosen;c.x.prepare(sw,dw);c.y.prepare(sh,dh);
        const uint8_t* middle=bgra;
        if(sw!=dw) {
            c.temporary.resize(size_t(dw)*sh*4);middle=c.temporary.data();
            for(int y=0;y<sh;++y)for(int x=0;x<dw;++x) {
                __m128i sum=_mm_set1_epi32(1<<21);
                const auto* src=bgra+(size_t(y)*sw+c.x.starts[x])*4;
                const auto* k=c.x.weights.data()+size_t(x)*c.x.stride;
                for(int i=0;i<c.x.counts[x];++i) {
                    uint32_t pixel;std::memcpy(&pixel,src+i*4,4);
                    auto channels=_mm_cvtepu8_epi32(_mm_cvtsi32_si128(pixel));
                    sum=_mm_add_epi32(sum,_mm_mullo_epi32(channels,_mm_set1_epi32(k[i])));
                }
                uint32_t pixel=pack_filtered(sum);
                std::memcpy(c.temporary.data()+(size_t(y)*dw+x)*4,&pixel,4);
            }
        }
        const auto swap=_mm_setr_epi8(2,1,0,3,6,5,4,7,10,9,8,11,14,13,12,15);
        for(int y=0;y<dh;++y) {
            auto* out=rgba+size_t(y)*dw*4;
            if(sh==dh) {
                const auto* src=middle+size_t(y)*dw*4;int x=0;
                for(;x+4<=dw;x+=4)_mm_storeu_si128((__m128i*)(out+x*4),_mm_shuffle_epi8(_mm_loadu_si128((const __m128i*)(src+x*4)),swap));
                for(;x<dw;++x){out[x*4]=src[x*4+2];out[x*4+1]=src[x*4+1];out[x*4+2]=src[x*4];out[x*4+3]=src[x*4+3];}
                continue;
            }
            const auto* k=c.y.weights.data()+size_t(y)*c.y.stride;
            int x=0;
            for(;x+2<=dw;x+=2) {
                __m256i sum=_mm256_set1_epi32(1<<21);
                for(int i=0;i<c.y.counts[y];++i) {
                    const auto* src=middle+(size_t(c.y.starts[y]+i)*dw+x)*4;
                    auto channels=_mm256_cvtepu8_epi32(_mm_loadl_epi64((const __m128i*)src));
                    sum=_mm256_add_epi32(sum,_mm256_mullo_epi32(channels,_mm256_set1_epi32(k[i])));
                }
                sum=_mm256_srai_epi32(sum,22);
                auto words=_mm_packus_epi32(_mm256_castsi256_si128(sum),_mm256_extracti128_si256(sum,1));
                auto bytes=_mm_packus_epi16(words,words);
                _mm_storel_epi64((__m128i*)(out+x*4),_mm_shuffle_epi8(bytes,swap));
            }
            for(;x<dw;++x) {
                __m128i sum=_mm_set1_epi32(1<<21);
                for(int i=0;i<c.y.counts[y];++i) {
                    uint32_t pixel;std::memcpy(&pixel,middle+(size_t(c.y.starts[y]+i)*dw+x)*4,4);
                    sum=_mm_add_epi32(sum,_mm_mullo_epi32(_mm_cvtepu8_epi32(_mm_cvtsi32_si128(pixel)),_mm_set1_epi32(k[i])));
                }
                auto bytes=_mm_shuffle_epi8(_mm_cvtsi32_si128(pack_filtered(sum)),swap);
                uint32_t pixel=_mm_cvtsi128_si32(bytes);std::memcpy(out+x*4,&pixel,4);
            }
        }
        return 1;
    }catch(...){return 0;}
}
