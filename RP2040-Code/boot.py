import storage

storage.remount("/", readonly=False)

m = storage.getmount("/")
m.label = "sashapi"
storage.remount("/", readonly=True)
