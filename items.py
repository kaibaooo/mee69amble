shop_items = []

class Item:
    def __init__(self, _name:str, _price:int, _usefunc:function) -> None:
        self.name = _name
        self.price = _price
        self.use = _usefunc

def coconut_use():
    pass
coconut = Item()