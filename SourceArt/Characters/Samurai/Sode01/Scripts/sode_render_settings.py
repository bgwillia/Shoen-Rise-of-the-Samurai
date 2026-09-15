"""Use an available Metal device for functional source review renders."""
import bpy


def configure(scene):
    prefs = bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        available = [d for d in prefs.devices if d.type == 'METAL']
        if available:
            for device in prefs.devices: device.use = device.type == 'METAL'
            scene.cycles.device = 'GPU'
            print('SODE_RENDER_DEVICE ' + ', '.join(d.name for d in available), flush=True)
            return
    except (TypeError, RuntimeError):
        pass
    scene.cycles.device = 'CPU'
    print('SODE_RENDER_DEVICE CPU', flush=True)
