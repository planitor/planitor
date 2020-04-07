from environs import Env
from hashids import Hashids
from reynir import Greynir

greynir = Greynir()
hashids = Hashids(salt="planitor", min_length=4)

env = Env()
env.read_env()
