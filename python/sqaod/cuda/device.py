import cuda_device
import sys

class Device :
    def __init__(self, devno) :
	self._cext = cuda_device # hold module while Device instance is active.
        # make ext as a member, and it should be initialized, 
        # since exception may occur in the nextline.
        self._ext = None
        self._ext = cuda_device.device_new(devno)

    def __del__(self) :
        if not self._ext is None :
            self.finalize();
	self._cext = None

    def finalize(self) :
        cuda_device.device_finalize(self._ext);
        cuda_device.device_delete(self._ext)
        self._ext = None
        
def create_device(devno = 0) :
    return Device(devno)


# Global/Static

this_module = sys.modules[__name__]

def unload() :
    if not this_module.active_device is None :
	this_module.active_device = None

if __name__ != "__main__" :
    this_module.active_device = create_device()
    import atexit
    atexit.register(unload)

