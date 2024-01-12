__author__ = "dgideas@outlook.com"
from typing import List, Tuple, Set, Optional, Dict
from uuid import uuid4
from dataclasses import dataclass
from secrets import randbelow, choice
from enum import Enum, IntEnum
from math import sqrt
import json
from datetime import date, timedelta
from collections import defaultdict

# Game basic configurations
MAP_X_LENGTH = 1024
MAP_Y_LENGTH = 1024
MAP_X_SPLIT = 4
MAP_Y_SPLIT = 4
STATION_NAMES_PREFIX = [*[""]*10, "新", "旧"]
STATION_NAMES = ["勿洛", "马泉营", "星达城", "西红门", "大红门", "佐敦", "尖沙咀", "旧宫", "新宫", "马家堡", "义顺", "顺义", "朝阳", "工人体育场", "爱情公寓", "莱佛士坊"]
STATION_NAMES_SUFFIX = [*[""]*10, "东", "南", "西", "北"]
GAS_FEE = 0.46
TRAIN_CAPACITY = 240
TICKET_PRICE = 12

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
        level_lhs = 6 - lhs_class.value # from station
        level_rhs = 6 - rhs_class.value # to station
        
        reverted = False
        if level_lhs > level_rhs:
            level_lhs, level_rhs = level_rhs, level_lhs
            reverted = True
        
        base_multiplier = 1 + level_lhs
        base_result = int(base_multiplier * level_rhs)
        if not reverted:
            return int(base_result*0.8), int(base_result*1.2)
        else:
            return int(base_result*0.64), int(base_result*0.8)

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
    
    @classmethod
    def get_maintance_fee(cls, station_class: "StationClassEnum") -> int:
        if station_class == cls.CLASS_1:
            return 250
        elif station_class == cls.CLASS_2:
            return 200
        elif station_class == cls.CLASS_3:
            return 150
        elif station_class == cls.CLASS_4:
            return 100
        elif station_class == cls.CLASS_5:
            return 50

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
    passengers: Dict[str, int] = None
    buy_pricing: int = None
    id: str = None
    name: str = None
    
    def __post_init__(self):
        self.id = str(uuid4())[-8:]
        if self.station_class:
            self.buy_pricing = StationClassEnum.get_random_price(self.station_class)
        self.passengers = defaultdict(lambda: 0)
    
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
    
    @classmethod
    def get_station_by_id(cls, stations: List["Station"], id: str) -> Optional["Station"]:
        for station in stations:
            if station.id == id:
                return station
        return None

    def __repr__(self) -> str:
        status_indicator = ""
        if self.status == StationStatusEnum.ST_ENABLED:
            status_indicator = "[OWNED]"
        passengers_info = []
        for passenger_destnation, passenger_count in self.passengers.items():
            passengers_info.append(f"To {passenger_destnation}: {passenger_count}")
        return f"<Station {self.id} {status_indicator}{self.name}(class {self.station_class}) price: {self.buy_pricing} {' '.join(passengers_info)}>"

@dataclass
class TrainV1(object):
    from_station: Station
    to_station: Station
    speed: int
    capacity: int
    ticket_price: int
    passengers: int = 0
    distance_travelled: int = 0
    
    def __repr__(self) -> str:
        distance = int(self.from_station.distance(self.to_station))
        return f"<Train ({(self.distance_travelled / distance * 100)}%) {self.passengers}/{self.capacity} from {self.from_station} to {self.to_station}>"

class Game(object):
    date: "date" = None
    map_regions: List[MapRegion] = None
    stations: List[Station] = None
    station_names: Set[str] = None
    trains_v1: List[TrainV1] = None
    money: int = 0 # Spent money for this train
    
    class OutOfMoneyException(Exception):
        pass
    
    def __init__(self) -> None:
        print("DGTrain Simulator 2024 v0.0.1")
        self.date = date.today()
        self.map_regions = []
        MapManager.init_map_regions(self.map_regions)
        
        self.stations = []
        self.station_names = set()
        
        for _ in range(10):
            self.stations.append(Station(pos_x=randbelow(MAP_X_LENGTH), pos_y=randbelow(MAP_Y_LENGTH), station_class=choice([c for c in StationClassEnum])))
            self.stations[-1].name = Station.generate_station_name(self.map_regions, self.stations[-1].pos_x, self.stations[-1].pos_y, self.station_names)
    
        self.money = 2000
        self.trains_v1 = []
    
    def _auto_train_v1(self):
        remaining_trains = []
        for train in self.trains_v1:
            train.distance_travelled += train.speed
            if train.distance_travelled > int(train.from_station.distance(train.to_station)):
                # Arrived
                earned = train.ticket_price * train.passengers
                print(f"Train {train} arrived at {train.to_station}, you've earned {earned}!")
                self.money += earned
            else:
                remaining_trains.append(train)
        self.trains_v1 = remaining_trains
    
    def _station_maintance(self):
        """Auto maintance station you owned on every month 1st"""
        if self.date.day != 1:
            return
        
        for station in self.stations:
            if station.status == StationStatusEnum.ST_ENABLED:
                maintance_fee = StationClassEnum.get_maintance_fee(station.station_class)
                print(f"Maintanced {station}, deducted fee: maintance_fee")
                self.money -= maintance_fee
    
    def _add_passenger(self):
        for from_station in self.stations:
            for to_station in self.stations:
                if from_station.id == to_station.id or from_station.status != StationStatusEnum.ST_ENABLED or to_station.status != StationStatusEnum.ST_ENABLED:
                    continue
                new_passengers_low, new_passengers_high = StationClassEnum.get_passenger_range(from_station.station_class, to_station.station_class)
                new_passengers = randbelow(new_passengers_high - new_passengers_low) + new_passengers_low
                from_station.passengers[to_station.id] += new_passengers
    
    def _check_money(self):
        if self.money < 0:
            raise self.OutOfMoneyException()
    
    def tick(self):
        try:
            self._auto_train_v1()
            self.date = self.date + timedelta(days=1)
            self._station_maintance()
            self._add_passenger()
            
            self._check_money()
        except self.OutOfMoneyException:
            print("You are bankrupted! Bye!")
            return -1
        return 0
    
    def gameloop(self) -> int:
        prompt = input(f"Today: {self.date.isoformat()} Money: {self.money} | a Calculator / s Show Stations / t Show Trains / g Create train / b Buy Station / c Continue / q Quit")
        if prompt == "s":
            for station in self.stations:
                print(station)
            return 0
        if prompt == "t":
            for train in self.trains_v1:
                print(train)
            return 0
        elif prompt == "c":
            pass
        elif prompt == "q":
            return -1
        elif prompt == "a":
            calc = input("Input two station ids to calculate its distance(split by space):")
            calc = calc.split(" ")
            if len(calc) != 2:
                return 0
            try:
                distance = Station.get_station_by_id(self.stations, calc[0]).distance(Station.get_station_by_id(self.stations, calc[1]))
            except:
                return 0
            print("Distance:", distance)
        elif prompt == "g":
            from_station_id = input("Input train from station id:")
            from_station: Station = Station.get_station_by_id(self.stations, from_station_id)
            print(f"From station: {from_station}")
            if not from_station:
                return 0
            to_station_id = input("Input to station id:")
            to_station: Station = Station.get_station_by_id(self.stations, to_station_id)
            print(f"To station: {to_station}")
            if not to_station:
                return 0
            cost = int(GAS_FEE * from_station.distance(to_station))
            delivered_passengers = min(TRAIN_CAPACITY, from_station.passengers[to_station_id])
            estimate_earned = TICKET_PRICE * delivered_passengers - cost
            prompt = input(f"Cost to perform this train is: {cost}$, to deliver {delivered_passengers} passengers, estimate_earned: {estimate_earned}, it's okay?(y/n)")
            if prompt == "y":
                self.money -= cost
                from_station.passengers[to_station_id] -= delivered_passengers
                self.trains_v1.append(TrainV1(from_station=from_station, to_station=to_station, speed=80, capacity=TRAIN_CAPACITY, ticket_price=TICKET_PRICE, passengers=delivered_passengers))
                print(f"[Announcement]Player have woohoo-ed {self.trains_v1[-1]} train! Congratulations!")
            return 0
        elif prompt == "b":
            station_id = input("Which station id you want to buy:")
            station: Station = Station.get_station_by_id(self.stations, station_id)
            if station.status == StationStatusEnum.ST_UNUSED:
                if self.money - station.buy_pricing < 0:
                    print("Too expensive!")
                    return 0
                confirm = input(f"Station {station.name} is {station.buy_pricing}$ If you buy, you will remain {self.money - station.buy_pricing}$, it's okay?(y/n)")
                if confirm == "y":
                    station.status = StationStatusEnum.ST_ENABLED
                    self.money -= station.buy_pricing
                    print(f"[Announcement]Player have bought {station.name} station! Congratulations!")
            else:
                print("Invalid.")
            return 0
        
        return self.tick()

def main():
    game = Game()
    while True:
        signal = game.gameloop()
        if signal != 0:
            break

if __name__ == "__main__":
    main()
