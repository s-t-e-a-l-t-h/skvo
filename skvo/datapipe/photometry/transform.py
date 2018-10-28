from datapipe.photometry import config as photometry_config
from utils import time_utils
from utils.special_characters import special_characters_encode
from skvo import settings


def prepare_message():
    pass


def get_photometry_loader(transform=None, init_sink=None):
    def load_photometry(start_date=None, end_date=None, **kwargs):
        sink = init_sink(**kwargs)
        sink()

    return load_photometry


def join_photometry_data(data, metadata):
    df = data.copy()
    meta_columns = metadata.columns
    for column in meta_columns:
        if column not in df:
            df[column] = metadata[column].iloc[0]
        else:
            raise ValueError("metadata dataframe contain same column name as observation data dataframe")
    return df


def get_tsdb_metric_name(target_catalogue_value, bandpass_uid):
    suffix = photometry_config.TSDB_METRIC_SUFFIX
    target_uid = special_characters_encode(target_catalogue_value)
    bandpass_uid = special_characters_encode(bandpass_uid)
    return '{}.{}.{}'.format(target_uid, bandpass_uid, suffix)


def photometry_timeseries_data_df_to_tsdb_metrics(df, source):
    df.reset_index(inplace=True, drop=True)
    df_timestamp = time_utils.parse_timestamp(df)
    timestamp = time_utils.pd_timestamp_to_unix(df_timestamp, unit='ms')

    metrics = [
        {
            'metric': get_tsdb_metric_name(df["target.catalogue_value"].iloc[i],
                                           df["bandpass.bandpass_uid"].iloc[i]),
            'timestamp': timestamp.iloc[i],
            'value': df["ts.magnitude"].iloc[i],
            'tags':
                {
                    'instrument': source,
                    'target': df["target.target"].iloc[0],
                    'source': source
                }
        }
        for i in range(timestamp.shape[0])
    ]

    return metrics


def photometry_exposute_data_df_to_tsdb_metrics(df, source):
    pass


def photometry_errors_data_df_to_tsdb_metrics(df, source):
    pass


def photometry_data_df_to_tsdb_meta_metrics(df, source):
    df.reset_index(inplace=True, drop=True)
    df_timestamp = time_utils.parse_timestamp(df)
    timestamp = time_utils.pd_timestamp_to_unix(df_timestamp, unit='ms')

    metrics = [
        {
            'metric': get_tsdb_metric_name(df["target.catalogue_value"].iloc[i],
                                           df["bandpass.bandpass_uid"].iloc[i]),
            'timestamp': timestamp.iloc[i],
            'value': df["ts.magnitude"].iloc[i],
            'tags':
                {
                    'instrument': source,
                    'target': df["target.target"].iloc[0],
                    'source': source,
                    'bandpass': df["bandpass.bandpass_uid"].iloc[i]
                }
        }
        for i in range(timestamp.shape[0])
    ]

    return metrics


def photometry_data_to_metadata_json(metadata_df, data_df, source):
    df = data_df.copy()
    df_timestamp = time_utils.parse_timestamp(df)
    timestamp = time_utils.pd_timestamp_to_unix(df_timestamp, unit='ms')
    df["ts.unix"] = timestamp

    metadata = \
        {
            "photometry": [
                {
                    "observation": {
                        "access": {
                            "access": metadata_df["access.access"].iloc[0]
                        },
                        "target": {
                            "target": metadata_df["target.target"].iloc[0],
                            "catalogue": metadata_df["target.catalogue"].iloc[0],
                            "catalogue_value": metadata_df["target.catalogue_value"].iloc[0],
                            "description": metadata_df["target.description"].iloc[0],
                            "right_ascension": metadata_df["target.right_ascension"].iloc[0],
                            "declination": metadata_df["target.declination"].iloc[0],
                            "target_class": metadata_df["target.target_class"].iloc[0]
                        },
                        "instrument": {
                            "instrument": metadata_df["instrument.instrument"].iloc[0],
                            "instrument_uid": metadata_df["instrument.instrument_uid"].iloc[0],
                            "telescope": metadata_df["instrument.telescope"].iloc[0],
                            "camera": metadata_df["instrument.camera"].iloc[0] or None,
                            "spectroscope": metadata_df["instrument.spectroscope"].iloc[0] or None,
                            "field_of_view": metadata_df["instrument.field_of_view"].iloc[0],
                            "description": metadata_df["instrument.description"].iloc[0]
                        },
                        "facility": {
                            "facility": metadata_df["facility.facility"].iloc[0],
                            "facility_uid": metadata_df["facility.facility_uid"].iloc[0],
                            "description": metadata_df["facility.description"].iloc[0]
                        },
                        "dataid": {
                            "title": metadata_df["dataid.title"].iloc[0],
                            "source": source,
                            "publisher": metadata_df["dataid.publisher"].iloc[0],
                            "publisher_did": metadata_df["dataid.publisher_did"].iloc[0],
                            "organisation": {
                                "organisation": metadata_df["organisation.organisation"].iloc[0],
                                "organisation_did": metadata_df["organisation.organisation_did"].iloc[0],
                                "email": metadata_df["organisation.email"].iloc[0]
                            }
                        }
                    },
                    "start_date": df["ts.timestamp"][df.first_valid_index()],
                    "end_date": df["ts.timestamp"][df.last_valid_index()],
                    "bandpass": {
                        "bandpass": metadata_df["bandpass.bandpass"].iloc[0],
                        "bandpass_uid": metadata_df["bandpass.bandpass_uid"].iloc[0],
                        "spectral_band_type": metadata_df["bandpass.spectral_band_type"].iloc[0],
                        "photometric_system": metadata_df["bandpass.photometric_system"].iloc[0]
                    },
                    "media": settings.SKVO_EXPORT_PATH
                }
            ]
        }

    return metadata


"""
json serializer:

{
   "photometry": [
       {
           "observation": {
               "access": {
                    "access": "on_demand"
               },
               "target": {
                   "target": "beta_Lyr",
                   "catalogue": "catalogue_name",
                   "catalogue_value": "catalogue_value",
                   "description": "desc",
                   "right_ascension": 0.1,
                   "declination": 0.2,
                   "raget_class": "binary"
               },
               "instrument": {
                   "instrument": "instrument_name",
                   "instrument_uid": "uid_for_instrument",
                   "telescope": "telescope",
                   "camera": "camera",
                   "spectroscope": "spectac",
                   "field_of_view": 10,
                   "description": "int desc"
               },
               "facility": {
                   "facility": "facility_name",
                   "facility_uid": "facility_uid",
                   "description": "fac desc"
               },
               "dataid": {
                   "title": "data id title",
                   "publisher": "data_id_publisher",
                   "publisher_did": "http://data_id_publisher",
                   "organisation": {
                       "organisation": "organisation_name_like",
                       "organisation_did": "http://organ",
                       "email": "email@google.com"
                   }
               }
           },
           "start_date": "2018-05-01T00:00:00",
           "end_date": "2018-05-04T00:00:00",
           "bandpass": {
               "bandpass": "bandpass_name",
               "bandpass_uid": "uid_for_band",
               "spectral_band_type": "optical",
               "photometric_system": "johnson"
           },
           "media": "/etc/sys/data"
       }
   ]
}
"""


def photometry_media_to_import_json(media_content, filename, data, metadata, source):
    import_json = {
        "content": media_content,
        "filename": filename,
        "source": source,
        "bandpass": None
    }

    return import_json
