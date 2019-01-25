class Landing():
    @classmethod
    def from_json(cls, landing_json):
        point = tuple(landing_json["point"])

        landing = cls(point)
        landing.value = landing_json["fitness"]

        return landing

    @classmethod
    def configure(
        cls,
        clearing_cost=500
    ):
        cls.clearing_cost = clearing_cost

    clearing_cost = 500
    def __init__(self, point):
        self.point = point
        self.value = 0

    def compute_value(self):
        self.value = 0 - Landing.clearing_cost

        return self.value
        
    def to_json(self):
        landing_json = {}

        landing_json["fitness"] = self.value
        landing_json["point"] = self.point

        return landing_json

    def __str__(self):
        return self.point.__str__()