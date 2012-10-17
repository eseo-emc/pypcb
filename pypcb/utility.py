class RotatableList(list):
    def __rshift__(self,steps):
        if steps > 1:
            return (self >> (steps-1)) >> 1
        elif steps == 1:
            return RotatableList([self[-1]] + self[:-1])
        elif steps == 0:
            return self
        else:
            raise ValueError
    def __lshift__(self,steps):
        if steps > 1:
            return (self << (steps-1)) << 1
        elif steps == 1:
            return RotatableList(self[1:] + [self[0]])
        elif steps == 0:
            return self
        else:
            raise ValueError