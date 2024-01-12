__author__ = "dgideas@outlook.com"
from typing import List, Tuple, Set, Optional
from uuid import uuid4
from dataclasses import dataclass
from secrets import randbelow, choice
from random import shuffle
from enum import Enum, IntEnum
from math import sqrt
import json

MAP_X_LENGTH = 1024
MAP_Y_LENGTH = 1024
MAP_X_SPLIT = 4
MAP_Y_SPLIT = 4
STATION_NAMES_PREFIX = [*[""]*10, "新", "旧"]
STATION_NAMES = ["勿洛", "马泉营", "星达城", "西红门", "大红门", "佐敦", "尖沙咀", "旧宫", "新宫", "马家堡", "义顺", "顺义", "朝阳", "工人体育场", "爱情公寓", "莱佛士坊"]
shuffle(STATION_NAMES)
STATION_NAMES_SUFFIX = [*[""]*10, "东", "南", "西", "北"]

class StationStatusEnum(Enum):
    ST_UNUSED = "unused"
    ST_ENABLED = "enabled"
    ST_DISABLED = "disabled"

class StationClassEnum(IntEnum):
    CLASS_1 = 1 # largest
    CLASS_2 = 2
    CLASS_3 = 3
    CLASS_4 = 4
    CLASS_5 = 5 # smallest
    
    @classmethod
    def get_passenger_range(cls, lhs_class: "StationClassEnum", rhs_class: "StationClassEnum") -> Tuple[int, int]:
        """Get daily passenger range by station classes(direction: lhs -> rhs), return [lower bound, upper bound]"""
        # TODO
        level_lhs = 6 - lhs_class.value # from station
        level_rhs = 6 - rhs_class.value # to station
        
        return 100
    
    @classmethod
    def get_random_price(cls, station_class: "StationClassEnum") -> Tuple[int, int]:
        """Get station random pricing by station class, return [lower bound, upper bound]"""
        level = 6 - station_class.value
        level_base_pricing = level * 270
        level_additional_pricing = randbelow(100 * level)
        return level_base_pricing + level_additional_pricing

    @classmethod
    def get_capacity(cls, station_class: "StationClassEnum") -> int:
        if station_class == cls.CLASS_1:
            return 1200
        elif station_class == cls.CLASS_2:
            return 900
        elif station_class == cls.CLASS_3:
            return 650
        elif station_class == cls.CLASS_4:
            return 400
        elif station_class == cls.CLASS_5:
            return 175

@dataclass
class MapRegion(object):
    start_x: int
    start_y: int
    name: str

class MapManager(object):
    @classmethod
    def map_x_split_length(cls) -> int:
        return int(MAP_X_LENGTH / MAP_X_SPLIT)
    
    @classmethod
    def map_y_split_length(cls) -> int:
        return int(MAP_Y_LENGTH / MAP_Y_SPLIT)
    
    @classmethod
    def choice_name(cls, exist_names: List[str]) -> str:
        while True:
            candidate_name = choice(STATION_NAMES)
            if candidate_name in exist_names:
                continue
            return candidate_name
    
    @classmethod
    def init_map_regions(cls, map_regions: List[MapRegion]):
        for x in range(MAP_X_SPLIT):
            for y in range(MAP_Y_SPLIT):
                map_regions.append(MapRegion(start_x=cls.map_x_split_length()*x, start_y=cls.map_y_split_length()*y, name=cls.choice_name([r.name for r in map_regions])))
    
    @classmethod
    def get_region_name(cls, x: int, y: int, map_regions: List[MapRegion]) -> Optional[str]:
        canonical_x = x - (x%cls.map_x_split_length())
        canonical_y = y - (y%cls.map_y_split_length())
        for region in map_regions:
            if region.start_x == canonical_x and region.start_y == canonical_y:
                return region.name
        return None

@dataclass
class Station(object):
    pos_x: int
    pos_y: int
    status: StationStatusEnum = StationStatusEnum.ST_UNUSED
    station_class: StationClassEnum = None
    buy_pricing: int = None
    id: str = None
    name: str = None
    
    def __post_init__(self):
        self.id = str(uuid4())
        if self.station_class:
            self.buy_pricing = StationClassEnum.get_random_price(self.station_class)
    
    def distance(self, rhs: "Station") -> float:
        """Calculate Euclidean distance between two stations"""
        return sqrt(pow((self.pos_x - rhs.pos_x), 2) + pow((self.pos_y - rhs.pos_y), 2))

    @classmethod
    def generate_station_name(cls, map_regions: List[MapRegion], pos_x: int, pos_y: int, exist_names: Optional[Set[str]] = None) -> str:
        def _generate_core():
            nonlocal map_regions, pos_x, pos_y
            return f"{choice(STATION_NAMES_PREFIX)}{MapManager.get_region_name(pos_x, pos_y, map_regions)}{choice(STATION_NAMES_SUFFIX)}"
        while True:
            candidate_name = _generate_core()
            if candidate_name[0] == candidate_name[1]: # avoid xxyz-formed name
                continue
            if exist_names and candidate_name in exist_names:
                continue
            if exist_names is not None:
                exist_names.add(candidate_name)
            return candidate_name

    def __repr__(self) -> str:
        return f"<Station {self.name}(class {self.station_class}) price: {self.buy_pricing} x: {self.pos_x}, y: {self.pos_y}>"

class Game(object):
    map_regions: List[MapRegion] = None
    stations: List[Station] = None
    station_names: Set[str] = None
    money: int = 0
    
    def __init__(self) -> None:
        self.map_regions = []
        MapManager.init_map_regions(self.map_regions)
        
        self.stations = []
        self.station_names = set()
        
        for _ in range(10):
            self.stations.append(Station(pos_x=randbelow(MAP_X_LENGTH), pos_y=randbelow(MAP_Y_LENGTH), station_class=choice([c for c in StationClassEnum])))
            self.stations[-1].name = Station.generate_station_name(self.map_regions, self.stations[-1].pos_x, self.stations[-1].pos_y, self.station_names)
    
        self.money = 1500
    
    def gameloop(self):
        ...

def main():
    game = Game()
    while True:
        game.gameloop()

if __name__ == "__main__":
    main()
