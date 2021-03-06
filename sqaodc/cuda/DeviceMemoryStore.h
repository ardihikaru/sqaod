#ifndef SQAOD_CUDA_DEVICEMEMORYSTORE_H__
#define SQAOD_CUDA_DEVICEMEMORYSTORE_H__

#include <map>
#include <set>
#include <sqaodc/cuda/DeviceObject.h>
#include <sqaodc/common/Array.h>

namespace sqaod_cuda {

namespace sq = sqaod;

/* ToDo: This implementatin is enough for now.  Will be reconsidered when needed. */

class HeapBitmap {
    typedef uint32_t  RegionBitmap;
    typedef std::set<uintptr_t> FreeRegions;
    typedef std::map<uintptr_t, RegionBitmap> RegionMap;

public:
    enum {
        nChunksInRegionInPo2 = 5,
        nChunksInRegion = 32,
        regionMask = 0x1fu,
    };

    HeapBitmap() { }

    void set(int chunkSizeShift)  {
        chunkSizeShift_ = chunkSizeShift;
        regionSize_ = nChunksInRegion << chunkSizeShift_;
    }

    void clear() {
        freeRegions_.clear();
        regions_.clear();
    }
    
    bool acquire(uintptr_t *addr);
    bool release(uintptr_t addr, uintptr_t *freeKey);

    void addRegion(uintptr_t addr);
    
private:
    bool isRegionFull(RegionBitmap region) const {
        return region == 0;
    }
    bool isRegionEmpty(RegionBitmap region) const {
        return (region & regionMask) == regionMask;
    }

    FreeRegions freeRegions_;
    RegionMap regions_;
    int chunkSizeShift_;
    int regionSize_;
};


class FixedSizedChunks {
public:
    void initialize();
    void finalize();

    size_t newHeapSize(size_t reqSize) const;

    void addFreeHeap(uintptr_t pv, size_t size);
    
    uintptr_t acquire(size_t *size);
    size_t release(uintptr_t addr, size_t size, uintptr_t *freeKey);

private:
    static
    int layerIdxFromSize(size_t size);
    static
    size_t layerIdxToChunkSize(int layerIdx);

    enum { nBitmapLayers = 11 };
    HeapBitmap bitmapLayers_[nBitmapLayers];

    typedef std::map<uintptr_t, size_t> AllocatedChunks;
};


class HeapMap {
public:
    HeapMap();
    
    void finalize();

    size_t newHeapSize();
    void addFreeHeap(uintptr_t addr, size_t size);
    
    uintptr_t acquire(size_t *size);    
    void release(uintptr_t addr, size_t size);
    
private:
    typedef std::map<uintptr_t, size_t> RegionMap;
    RegionMap freeRegions_;
    size_t currentHeapSize_;
};


class DeviceMemoryStore {
    /* Memory chunks whose capacity is less than / equals to 256 MBytes are managed by memory store.
     * Chunks larger than 512 MB directly use cudaMalloc()/cudaFree(). */ 
    enum {
        ChunkSizeToUseMalloc = 64 * (1 << 20), /* 64 M */
        SmallChunkSize = 4 * (1 << 10),        /*  4 K */
    };
public:
    DeviceMemoryStore();

    void initialize();
    void finalize();
    
    void useManagedMemory(bool use);

    void enableLocalStore(bool enable);

    void *allocate(size_t size);
    void deallocate(void *pv);

private:
    bool initialized_;
    bool useManagedMemory_;
    bool enableLocalStore_;

    uintptr_t cudaMalloc(size_t size);
    void cudaFree(void *pv);

    uintptr_t allocFromHeapMap(size_t *size);
    void deallocateInHeapMap(uintptr_t addr, size_t size);
    
    uintptr_t allocFromFixedSizedChunks(size_t *size);
    void deallocateInFixedSizedChunks(uintptr_t addr, size_t);
    
    /* Custom memory region manager */
    HeapMap heapMap_;
    FixedSizedChunks fixedSizedChunks_;
    /* Chunks allocated by cudaMalloc(). */
    sq::ArrayType<void*> d_mems_;

    enum HeapSource {
        fromNone = 0,
        fromFixedSizedSeries = 1,
        fromHeapMap = 2,
        fromCudaMalloc = 3,
    };

    struct ChunkProp {
        ChunkProp() { }
        ChunkProp(uintptr_t _addr, size_t _size, enum HeapSource _src)
                : addr(_addr), size(_size), src(_src) { }
        uintptr_t addr;
        size_t size;
        enum HeapSource src;
    };

    struct ChunkPropLess {
        bool operator()(const ChunkProp &lhs, const ChunkProp &rhs) const {
            return lhs.addr < rhs.addr;
        }
    };

    /* FIXME: use hash_map ? */
    typedef std::set<ChunkProp, ChunkPropLess> ChunkPropSet;
    ChunkPropSet chunkPropSet_;
};

}

#endif
