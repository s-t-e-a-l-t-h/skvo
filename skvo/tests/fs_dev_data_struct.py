import datetime
import logging
import os
import random
import re
import pylab as plt
import numpy as np
import pandas as pd
from pandas.io import json

from datapipe.photometry.filesystem import parse_bandpass_uid_from_path
from datapipe.photometry.filesystem import parse_target_from_path

# quick log settings
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s : [%(levelname)s] : %(name)s : %(message)s')
logger = logging.getLogger(__name__)

RAs = {"W_UMa": 145.93, "bet_Per": 40.95, "bet_Lyr": 282.51}
DEs = {"W_UMa": 55.95, "bet_Per": 47.04, "bet_Lyr": 33.36}

MOCK_DATA_LENGTH = 15
DEFAULT_BASE_PATH = os.path.join(os.path.expanduser("~/"), "skvo_data")
CATALOGUE = "default"
DEFAULT_DEV_DATA_STRUCT = {
    "upjs": {
        "photometry": {
            "media": {
                "201712": {
                    "bet_Per_20171202": {"johnson.u", "sloan.u"},
                    "bet_Lyr_20171204": {"johnson.u", "sloan.u"},
                    "W_UMa_20171204": {"johnson.u", "sloan.u"}
                },
                "201801": {
                    "bet_Per_20180102": {"johnson.u", "sloan.u"},
                    "bet_Lyr_20180102": {"johnson.u", "sloan.u"},
                    "W_UMa_20180103": {"johnson.u", "sloan.u"}
                },
                "201802": {
                    "bet_Per_20180202": {"johnson.u", "sloan.u"},
                    "bet_Lyr_20180202": {"johnson.u", "sloan.u"},
                    "W_UMa_20180202": {"johnson.u", "sloan.u"}
                }
            },
            "dtables": {
                "201712": {
                    "bet_Per_20171202": {"johnson.u", "sloan.u"},
                    "bet_Lyr_20171204": {"johnson.u", "sloan.u"},
                    "W_UMa_20171204": {"johnson.u", "sloan.u"}
                },
                "201801": {
                    "bet_Per_20180102": {"johnson.u", "sloan.u"},
                    "bet_Lyr_20180102": {"johnson.u", "sloan.u"},
                    "W_UMa_20180103": {"johnson.u", "sloan.u"}
                },
                "201802": {
                    "bet_Per_20180202": {"johnson.u", "sloan.u"},
                    "bet_Lyr_20180202": {"johnson.u", "sloan.u"},
                    "W_UMa_20180202": {"johnson.u", "sloan.u"}
                }

            }
        },
        "spectroscopy": {
            "media": {
                "201801": {"bet_Per_20180102", "bet_Lyr_20180105"},
                "201802": {"bet_Per_20180202", "bet_Lyr_20180216"}
            },
            "dtables": {
                "201801": {"bet_Per_20180102", "bet_Lyr_20180105"},
                "201802": {"bet_Per_20180202", "bet_Lyr_20180216"}

            }
        }
    },
    "vhao": {
        "photometry": {
            "media": {
                "201712": {
                    "bet_Lyr_20171221": {"sdss.g"},
                    "W_UMa_20171204": {"bessel.r"}
                },
            },
            "dtables": {
                "201712": {
                    "bet_Lyr_20171221": {"sdss.g"},
                    "W_UMa_20171204": {"bessel.r"}
                },
            }
        },
    }
}


def expand_dict(d):
    result = list()
    df = json.json_normalize(d, sep=os.sep)
    d = df.to_dict(orient='records')[0]
    for k, v in d.items():
        for _v in v:
            result.append(os.path.join(k, _v))
    return result


def prepare_base_path():
    if not os.path.isdir(DEFAULT_BASE_PATH):
        logger.info("Creating path {}".format(DEFAULT_BASE_PATH))
        os.makedirs(DEFAULT_BASE_PATH)
    else:
        logger.info("Path {} already exists".format(DEFAULT_BASE_PATH))


def prepare_data_struct():
    paths = expand_dict(DEFAULT_DEV_DATA_STRUCT)
    logger.info("Creating data paths")
    for path in paths:
        path = os.path.join(DEFAULT_BASE_PATH, path)
        os.makedirs(path, exist_ok=True)


def fill_basic_photometry_dtable_df(startdate):
    df = pd.DataFrame()
    df["ts.timestamp"] = [startdate + datetime.timedelta(seconds=i) for i in range(MOCK_DATA_LENGTH)]
    df["ts.magnitude"] = [random.randint(1, 10) / float(random.randint(10, 20)) for _ in range(MOCK_DATA_LENGTH)]
    df["ts.magnitude_error"] = [random.randint(1, 10) / float(random.randint(10, 20)) for _ in range(MOCK_DATA_LENGTH)]
    df["ts.flux_calibration"] = "abs"
    df["ts.flux_calibration_level"] = random.randint(1, 5)
    df["ts.exposure"] = random.randint(10, 60)
    df["ts.timeframe_reference_position"] = "heliocenter"
    return df


def fill_basic_photometry_metatable_df(path):
    df = pd.Series()
    target = parse_target_from_path(path)
    target_ra, target_de = RAs[target], DEs[target]
    band = parse_bandpass_uid_from_path(path)
    instrument = "xyz" if target in ["W_UMa"] else "uvw"
    source = parse_source_from_path(path)

    df["target.target"] = target
    df["target.catalogue"] = CATALOGUE
    df["target.catalogue_value"] = "{}".format(target)
    df["target.description"] = "{} description".format(target)
    df["target.right_ascension"] = target_ra
    df["target.declination"] = target_de
    df["target.equinox"] = "J2000"
    df["target.target_class"] = "variable"

    df["bandpass.bandpass"] = "band.{}".format(band)
    df["bandpass.bandpass_uid"] = band
    df["bandpass.spectral_band_type"] = "optical"
    df["bandpass.photometric_system"] = "sys"

    df["instrument.instrument"] = "instrument.{}".format(instrument)
    df["instrument.telescope"] = "instrument.telescope.{}".format(instrument)
    df["instrument.camera"] = "instrument.camera.{}".format(instrument)
    df["instrument.spectroscope"] = "instrument.spect.{}".format(instrument)
    df["instrument.field_of_view"] = random.randint(10, 12)
    df["instrument.description"] = "instrument.description"

    df["facility.facility"] = "facility.in.{}".format(source)
    df["facility.facility_uid"] = "uid.facility.{}".format(source)
    df["facility.description"] = "facility.description.{}".format(source)

    df["organisation.organisation"] = "organisation.{}".format(source)
    df["organisation.organisation_did"] = "http://organisation.did.{}".format(source)
    df["organisation.email"] = "{}@{}.com".format(source, source)

    df["dataid.title"] = "title.{}".format(source)
    df["dataid.publisher"] = "publisher.{}".format(source)
    df["dataid.publisher_did"] = "http://publisher_did.{}".format(source)

    df["access.access"] = "open"
    return pd.DataFrame(df).T


def prepare_photometry_dtables():
    paths = expand_dict(DEFAULT_DEV_DATA_STRUCT)

    return {path: fill_basic_photometry_dtable_df(
        parse_datetime_from_path(path) + datetime.timedelta(seconds=1))
        for path in paths if "photometry" in path and "media" not in path}


def prepare_photometry_metatables():
    paths = expand_dict(DEFAULT_DEV_DATA_STRUCT)
    return {path: fill_basic_photometry_metatable_df(path)
            for path in paths if "photometry" in path and "media" not in path}


def prepare_photometry_media():
    paths = expand_dict(DEFAULT_DEV_DATA_STRUCT)
    return {path: {"{}.png".format(idx): generate_random_image() for idx in range(MOCK_DATA_LENGTH)}
            for path in paths if "photometry" in path and "media" in path}


def parse_datetime_from_path(path):
    dt = path.split(os.sep)[-2].split("_")[-1]
    rs = re.search(r"([0-9]{4})([0-9]{2})([0-9]{2})", dt)
    return datetime.datetime(int(rs[1]), int(rs[2]), int(rs[3]))


def parse_tablename_from_path(path):
    return path.split(os.sep)[-2]


def parse_source_from_path(path):
    return path.split(os.sep)[0]


def prepare_data():
    logger.info("Preparing mock data")
    p_dtables = prepare_photometry_dtables()
    p_metatables = prepare_photometry_metatables()
    p_media = prepare_photometry_media()

    for key in p_dtables.keys():
        metatable_path = os.path.join(DEFAULT_BASE_PATH, key, "{}_meta.csv".format(parse_tablename_from_path(key)))
        dtable_path = os.path.join(DEFAULT_BASE_PATH, key, "{}_data.csv".format(parse_tablename_from_path(key)))
        p_dtables[key].to_csv(dtable_path, index=False)
        p_metatables[key].to_csv(metatable_path, index=False)

    for path_to_band_dir, media in p_media.items():
        for png, img in media.items():
            date = parse_datetime_from_path(path_to_band_dir)
            date_suffix = "{}".format(datetime.datetime.strftime(date, "%Y%m%d"))

            path = os.path.join(DEFAULT_BASE_PATH, path_to_band_dir, "{}_{}".format(date_suffix, png))
            save_image(path, img)
    logger.debug("Done")


def generate_random_image():
    matrix = np.random.random((5, 5))
    return matrix


def save_image(path, img):
    plt.imshow(img, cmap='gray', interpolation='nearest')
    plt.savefig(path)


def main():
    random.seed(10)
    prepare_base_path()
    prepare_data_struct()
    prepare_data()


if __name__ == "__main__":
    main()
