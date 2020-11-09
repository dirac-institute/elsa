import psutil

def get_mem_limit(rss):
    # print(rss)
    return psutil.virtual_memory().total

c.ResourceUseDisplay.mem_limit = get_mem_limit