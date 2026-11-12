"""One proportional 16:9 content area for drawing and pointer hit tests."""
def content_bounds(width,height):
    unit=min(width/16,height/9)
    w=max(1,round(16*unit));h=max(1,round(9*unit))
    return (width-w)//2,(height-h)//2,w,h

def content_point(point,bounds):
    return point[0]-bounds[0],point[1]-bounds[1]
