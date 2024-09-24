from dataclasses import dataclass
import csv

# fmt: off
E24 = [
    1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
    3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1
]

E48 = [
    1.00, 1.05, 1.10, 1.15, 1.21, 1.27, 1.33, 1.40, 1.47, 1.54,
    1.62, 1.69, 1.78, 1.87, 1.96, 2.05, 2.15, 2.26, 2.37, 2.49,
    2.61, 2.74, 2.87, 3.01, 3.16, 3.32, 3.48, 3.65, 3.83, 4.02,
    4.22, 4.42, 4.64, 4.87, 5.11, 5.36, 5.62, 5.90, 6.19, 6.49,
    6.81, 7.15, 7.50, 7.87, 8.25, 8.66, 9.09, 9.53
]
# fmt: on


@dataclass
class DatabaseRow:
    part_id: str
    value: str
    component: str
    manufacturer: str
    manufacturer_part_number: str
    rating: str
    package: str
    lcsc: str
    or_equivalent: str
    symbol: str
    footprint: str
    datasheet: str

    def values(self):
        return iter(vars(self).values())

    def headers(self):
        return iter(vars(self).keys())


@dataclass
class YageoResistor:
    resistance: float
    package: str
    tolerance: float

    def __post_init__(self):
        DATASHEET = "https://www.yageo.com/upload/media/product/products/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf"
        MANUFACTURER = "Yageo"
        SYMBOL = "Device:R_Small"
        POWER = "0.1W"
        self.database_row = DatabaseRow(
            part_id=resistor_part_id_str(
                resistance=self.resistance,
                package=self.package,
                tolerance=self.tolerance,
            ),
            datasheet=DATASHEET,
            symbol=SYMBOL,
            footprint=resistor_footprint_str(self.package),
            value=resistor_value_str(self.resistance),
            component=resistor_description_str(
                resistance=self.resistance,
                package=self.package,
                tolerance=self.tolerance,
            ),
            manufacturer=MANUFACTURER,
            manufacturer_part_number=yageo_resistor_mpn(
                resistance=self.resistance,
                package=self.package,
                tolerance=self.tolerance,
            ),
            rating=f"{resistor_tolerance_str(self.tolerance)}, {POWER}",
            package=self.package,
            lcsc="",
            or_equivalent="y",
        )


def resistor_tolerance_str(tolerance: float):
    """
    1.0 -> 1%
    0.5 -> 0.5%
    """
    return f"{tolerance:.1f}".rstrip("0").rstrip(".") + "%"


def resistor_part_id_str(resistance: float, package: str, tolerance: float):
    """
    R-10k-0603-1%
    """
    return f"R-{resistor_value_str(resistance)}-{package}-{resistor_tolerance_str(tolerance)}"


def resistor_footprint_str(package: str):
    if package == "0402":
        return "Resistor_SMD:R_0402_1005Metric"
    elif package == "0603":
        return "Resistor_SMD:R_0603_1608Metric"
    else:
        raise ValueError("Invalid package type")


def resistor_value_str(resistance: float):
    """
    0.1 -> 0.1
    10 -> 10
    1000 -> 1k
    2500 -> 2.5k
    1000000 -> 1M
    10.234 -> 10.23
    """
    magnitude = ""

    if resistance >= 1_000_000:
        magnitude = "M"
        resistance = resistance / 1_000_000
    elif resistance >= 1_000:
        magnitude = "k"
        resistance = resistance / 1_000

    return f"{resistance:.2f}".rstrip("0").rstrip(".") + magnitude


def resistor_description_str(resistance: float, package: str, tolerance: float):
    """
    10k 0402 1% 0.1W
    """
    return f"Resistor {resistor_value_str(resistance)} {package} {resistor_tolerance_str(tolerance)} 0.1W"


def yageo_resistor_mpn(
    resistance: float, package: str = "0603", tolerance: float = 1.0
) -> str:
    """
    Generates a Yageo surface mount resistor part number from a given resistance value.

    See the following document for detailed part number description:
    https://www.yageo.com/upload/media/product/products/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf
    """
    # R=Paper taping reel
    PACKAGING = "R"
    # 07=7", 10=10", 13=13"
    REEL = "07"

    if resistance < 1_000:
        magnitude = "R"
    elif resistance < 1_000_000:
        magnitude = "K"
        resistance = resistance / 1_000
    elif resistance <= 10_000_000:
        magnitude = "M"
        resistance = resistance / 1_000_000
    else:
        raise ValueError("Not a valid resistance value (1 < {} < 10,000,000)")

    # Strip trailing zeroes and replace decimal point with magnitude letter
    resistance_str = f"{resistance:.2f}".rstrip("0").replace(".", magnitude)

    if package not in ["0201", "0402", "0603", "0805", "1206", "1210"]:
        raise ValueError("Invalid package")

    if tolerance == 1.0:
        tolerance_str = "F"
    elif tolerance == 5.0:
        tolerance_str = "J"
    else:
        raise ValueError("Invalid tolerance, must be 1.0% or 5.0%")

    return f"RC{package}{tolerance_str}{PACKAGING}-{REEL}{resistance_str}L"


def resistor_list(
    package: str, tolerance: float, series: list[float], decades: list[int]
):
    resistors = []
    for decade in decades:
        for base in series:
            resistance = base * decade
            resistors.append(
                YageoResistor(
                    resistance=resistance, package=package, tolerance=tolerance
                )
            )

    return resistors


def gen_resistor_csv():
    packages = ["0402", "0603"]
    series_tolerances = [(E48, 1.0), (E24, 5.0)]
    decades = [1, 10, 100, 1_000, 10_000, 100_000, 1_000_000]

    resistors = []
    for package in packages:
        for series, tolerance in series_tolerances:
            resistors += resistor_list(
                package=package, tolerance=tolerance, series=series, decades=decades
            )

    resistors += [
        YageoResistor(resistance=0.0, package="0402", tolerance=5.0),
        YageoResistor(resistance=0.0, package="0603", tolerance=5.0),
        YageoResistor(resistance=10_000_000, package="0402", tolerance=1.0),
        YageoResistor(resistance=10_000_000, package="0603", tolerance=1.0),
    ]

    with open("yageo_resistors.csv", "w") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(resistors[0].database_row.headers())
        for resistor in resistors:
            writer.writerow(resistor.database_row.values())


if __name__ == "__main__":
    gen_resistor_csv()
