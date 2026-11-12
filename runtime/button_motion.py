"""Dreams BokehButton's traced hover-size update (0x7429218–0x7429279)."""
class ButtonMotion:
    def __init__(self):self.scales={};self.phase=0.
    def update(self,buttons,point,dt):
        self.phase+=min(.1,dt)
        while self.phase>=1/30:
            self.phase-=1/30
            for name,rect in buttons.items():
                radius=.22 if name=='imps' else .20
                target=1+.005/radius if rect.collidepoint(point) else 1.
                old=self.scales.get(name,1.)
                self.scales[name]=old+(target-old)*.20000000298023224
        return self.scales
