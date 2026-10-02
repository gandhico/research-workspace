module DVSLoader

using CUDA
using HDF5
using Base.Threads

export DvsBufferPool, start_prefetcher!, fetch_next_batch!

# ==============================================================================
# 1. The Pinned Memory Structure
# ==============================================================================
"""
    PinnedBatch{T}

A strictly typed data structure allocated entirely in page-locked (pinned) 
host memory. This prevents the OS from swapping the memory to disk and 
allows CUDA to execute hyper-fast, asynchronous DMA transfers over the PCIe bus.
"""
struct PinnedBatch{T}
    data::Array{T, 3}      # [Spatial_Dim, Time_Steps, Batch_Size]
    targets::Array{T, 2}   # [Classes, Batch_Size]
end

function PinnedBatch(spatial_dim::Int, time_steps::Int, classes::Int, batch_size::Int)
    # CUDA.Mem.pin registers standard Julia arrays into page-locked host memory
    data = CUDA.Mem.pin(zeros(Float32, spatial_dim, time_steps, batch_size))
    targets = CUDA.Mem.pin(zeros(Float32, classes, batch_size))
    return PinnedBatch(data, targets)
end

# ==============================================================================
# 2. The Buffer Pool Manager
# ==============================================================================
"""
    DvsBufferPool

Manages the double-buffering queues to completely eradicate memory allocation 
during the training loop. The CPU and GPU trade these buffers back and forth.
"""
struct DvsBufferPool
    ready_queue::Channel{PinnedBatch{Float32}}
    recycle_queue::Channel{PinnedBatch{Float32}}
    
    # Persistent GPU Tensors (Pre-allocated once)
    gpu_data::CuArray{Float32, 3}
    gpu_targets::CuArray{Float32, 2}
    
    # Structural metadata
    batch_size::Int
    spatial_dim::Int
    time_steps::Int
end

function DvsBufferPool(; spatial_dim=1024, time_steps=60, classes=11, batch_size=32, buffer_count=3)
    ready = Channel{PinnedBatch{Float32}}(buffer_count)
    recycle = Channel{PinnedBatch{Float32}}(buffer_count)
    
    # Pre-populate the recycle queue with pinned memory
    for _ in 1:buffer_count
        put!(recycle, PinnedBatch(spatial_dim, time_steps, classes, batch_size))
    end
    
    # Allocate the master GPU receivers
    gpu_data = CUDA.zeros(Float32, spatial_dim, time_steps, batch_size)
    gpu_targets = CUDA.zeros(Float32, classes, batch_size)
    
    return DvsBufferPool(ready, recycle, gpu_data, gpu_targets, batch_size, spatial_dim, time_steps)
end

# ==============================================================================
# 3. The Asynchronous Worker Thread
# ==============================================================================
"""
    start_prefetcher!(pool, filepath)

Spawns a background CPU thread that continuously reads from the HDF5 file, 
downsamples the spatial dimensions, and fills the pinned buffers. 
It will block automatically if the `ready_queue` is full, ensuring it doesn't 
overrun the GPU.
"""
function start_prefetcher!(pool::DvsBufferPool, filepath::String)
    Threads.@spawn begin
        println("[IO Thread] Prefetcher started...")
        
        # Open the file ONCE in the background thread
        fid = h5open(filepath, "r")
        raw_dataset = fid["X_train"] 
        raw_targets = fid["y_train"]
        
        total_samples = size(raw_targets, 1)
        num_batches = div(total_samples, pool.batch_size)
        
        for batch_idx in 1:num_batches
            # 1. Grab an empty, pre-allocated buffer from the recycle bin
            buffer = take!(pool.recycle_queue)
            
            start_idx = (batch_idx - 1) * pool.batch_size + 1
            end_idx = batch_idx * pool.batch_size
            
            # 2. Extract and downsample the HDF5 chunk directly into the pinned buffer
            # (In reality, your downsample() and one_hot_11() logic goes right here)
            # Example mock load:
            buffer.data .= read(raw_dataset, :, :, start_idx:end_idx) 
            # ... process targets into one-hot ...
            
            # 3. Push the populated buffer to the ready queue for the GPU
            put!(pool.ready_queue, buffer)
        end
        
        close(fid)
        println("[IO Thread] Prefetching complete.")
    end
end

# ==============================================================================
# 4. The Main Thread Consumer
# ==============================================================================
"""
    fetch_next_batch!(pool)

Called inside the main GPU training loop. Pulls the next pre-processed frame 
from the ready queue, executes a non-blocking DMA transfer to the GPU, and 
returns the empty host buffer to the worker thread.
"""
function fetch_next_batch!(pool::DvsBufferPool)
    # 1. Block until the CPU worker has a frame ready
    populated_buffer = take!(pool.ready_queue)
    
    # 2. Asynchronous DMA transfer from pinned host memory to GPU VRAM
    copyto!(pool.gpu_data, populated_buffer.data)
    copyto!(pool.gpu_targets, populated_buffer.targets)
    
    # 3. Return the host buffer back to the worker thread for the next chunk
    put!(pool.recycle_queue, populated_buffer)
    
    # 4. Return the pointers to the now-populated GPU arrays
    return pool.gpu_data, pool.gpu_targets
end

end # module