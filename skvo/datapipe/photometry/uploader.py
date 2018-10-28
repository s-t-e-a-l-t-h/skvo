import argparse
import logging
import os
import datetime

from conf import config
from datapipe.photometry import filesystem as fs
from datapipe.photometry import read
from datapipe.photometry import transform
from datapipe.importers import MetadataHttpImporter, OpenTsdbHttpImporter, MediaHttpImporter


class PhotometryProcessor(object):
    def __init__(self):
        pass


def run():
    config.set_up_logging()
    logger = logging.getLogger('photometry-uploader')
    logger.info("running photometry uploader")

    sources = fs.get_sources(config.BASE_PATH)
    data_locations = fs.get_data_locations(config.BASE_PATH, sources)

    metadata_importer = MetadataHttpImporter(server="localhost:8082")
    tsdb_importer = OpenTsdbHttpImporter(server=config.OPENTSDB_SERVER, batch_size=config.OPENTSDB_BATCH_SIZE)
    media_importer = MediaHttpImporter(server="localhost:8082")

    for source, dtables_paths in data_locations.items():
        for dtables_path in dtables_paths:
            full_dtables_path = fs.normalize_path(os.path.join(config.BASE_PATH, dtables_path))
            bandpass_fs_uid = fs.parse_bandpass_uid_from_path(dtables_path)
            target_fs_uid = fs.parse_target_from_path(dtables_path)
            start_date = fs.parse_date_from_path(dtables_path)
            dtable_name = fs.get_dtable_name_from_path(full_dtables_path)
            metatable_name = fs.get_metatable_name_from_path(full_dtables_path)
            full_media_path = fs.get_corresponding_media_path(full_dtables_path)

            logger.debug("reading metadata and data for object: {}, datetime: {}, bandpass: {}, source: {}"
                         "".format(target_fs_uid, datetime.date.strftime(start_date, "%Y-%m-%d"),
                                   bandpass_fs_uid, source))

            metadata = read.read_csv_file(os.path.join(full_dtables_path, metatable_name))
            data = read.read_csv_file(os.path.join(full_dtables_path, dtable_name))
            all_df = transform.join_photometry_data(data, metadata)

            metadata_json = transform.photometry_data_to_metadata_json(metadata, data, source)

            print(metadata_json)

            # tsdb_metrics = transform.photometry_timeseries_data_df_to_tsdb_metrics(df, source)

            # metadata_importer.imp(metadata_json)
            # tsdb_importer.imp(tsdb_metrics)

            # media_files = fs.get_media_list_on_path(full_media_path)
            # for mf in media_files:
            #     full_media_file_path = os.path.join(full_media_path, mf)
            #     media_file_content = fs.read_file_as_binary(full_media_file_path)
            #     import_content_json = \
            #         transform.photometry_media_to_import_json(media_file_content, mf, metadata, data, source)
            #     media_importer.imp(import_content_json)
            #

    # photometry_loader = transform.get_photometry_loader(transform=None, init_sink=None)


def main():
    parser = argparse.ArgumentParser(description="")

    parser.add_argument('--config', nargs='?', help='path to configuration file')
    parser.add_argument('--log', nargs='?', help='path to json logging configuration file')

    parser.add_argument('--tsdb-server', nargs='?', help='TSD host name.')
    parser.add_argument('--tsdb-batch-size', nargs='?', type=int, help='maximum batch size for OpenTSDB http input')

    parser.add_argument('--base-path', nargs='?', type=str, help='base path to data storage')

    args = parser.parse_args()

    if args.config:
        config.read_and_update_config(args.config)

    config.CONFIG_FILE = args.config or config.CONFIG_FILE
    config.LOG_CONFIG = args.log or config.LOG_CONFIG

    config.OPENTSDB_SERVER = args.tsdb_server or config.OPENTSDB_SERVER
    config.OPENTSDB_BATCH_SIZE = args.tsdb_batch_size or config.OPENTSDB_BATCH_SIZE

    config.BASE_PATH = args.base_path or config.BASE_PATH
    config.set_up_logging()

    run()

if __name__ == '__main__':
    main()
