import argparse
import logging
import os
import shutil
import time

from tqdm import tqdm


def setup_logging():
    """
    Set up logging to a file and console.
    Returns the logger instance.
    """
    log_file = f"move_dcm_files_{time.strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    return logger


def list_patient_directories(
    disk_path: str, sort: bool = True, logger: logging.Logger = None
):
    """
    List all patient directories in the given disk path.
    Optionally sort the directories.
    Logs the number of directories found.
    """
    try:
        patient_dirs = [
            d
            for d in os.listdir(disk_path)
            if os.path.isdir(os.path.join(disk_path, d))
        ]
        logger.info(f"Found {len(patient_dirs)} patient directories.")
        if sort:
            patient_dirs.sort()
        return patient_dirs
    except Exception as e:
        logger.error(f"Error listing patient directories: {e}")
        return []


def list_dcm_files(patient_path: str, file_extension: str):
    """
    List all DCM files in the patient directory with the specified file extension.
    Returns a list of file paths.
    """
    patient_dcm_files = []
    for root, _, files in os.walk(patient_path):
        for file in files:
            if file.endswith(file_extension):
                patient_dcm_files.append(os.path.join(root, file))
    return patient_dcm_files


def move_dcm_files(
    patient_dcm_files: list, patient_path: str, logger: logging.Logger = None
):
    """
    Move DCM files to the patient directory.
    Logs the process and handles errors.
    Returns the count of moved files.
    """
    moved_files_count = 0
    for dcm_file in patient_dcm_files:
        try:
            destination_path = os.path.join(patient_path, os.path.basename(dcm_file))
            if not os.path.exists(destination_path):
                shutil.move(dcm_file, destination_path)
                moved_files_count += 1
                time.sleep(0.01)  # Sleep for 10 ms to avoid overloading the system
            else:
                logger.warning(f"File {destination_path} already exists. Skipping.")
        except Exception as e:
            logger.error(f"Error moving file {dcm_file}: {e}")
    return moved_files_count


def process_patient_directory(
    disk_path: str, patient_dir: str, file_extension: str, logger: logging.Logger = None
):
    """
    Process a single patient directory:
    - List DCM files
    - Move DCM files to the patient directory
    - Log the number of files before and after moving
    """
    patient_path = os.path.join(disk_path, patient_dir)
    patient_dcm_files = list_dcm_files(patient_path, file_extension)

    if not patient_dcm_files:
        logger.info(f"{patient_dir}: No DCM files found.")
        return 0

    logger.info(
        f"{patient_dir}: {len(patient_dcm_files)} DCM files found before moving."
    )

    moved_files_count = move_dcm_files(patient_dcm_files, patient_path, logger=logger)

    new_dcm_files_count = len(
        [name for name in os.listdir(patient_path) if name.endswith(file_extension)]
    )
    logger.info(f"{patient_dir}: {new_dcm_files_count} DCM files after moving.")
    logger.info(f"{patient_dir}: {moved_files_count} DCM files were moved.")

    return moved_files_count


def main():
    """
    Main function to parse arguments, set up logging, and process patient directories.
    Logs the start and end time of the execution.
    """
    start_time = time.time()

    parser = argparse.ArgumentParser(
        description="Move DCM files to their respective directories."
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to the disk containing patient directories",
    )
    parser.add_argument(
        "--extension",
        "-e",
        type=str,
        default=".dcm",
        help="File extension to look for (default: .dcm)",
    )
    args = parser.parse_args()

    logger = setup_logging()

    disk_path = args.path
    file_extension = args.extension

    logger.info(f"Moving DCM files from {disk_path} with extension {file_extension}")

    patients = list_patient_directories(disk_path, sort=True, logger=logger)

    total_moved_files = 0
    for patient_dir in tqdm(patients, desc="Moving DCM files", unit="patient"):
        moved_files_count = process_patient_directory(
            disk_path, patient_dir, file_extension, logger=logger
        )
        total_moved_files += moved_files_count

    end_time = time.time()
    duration = end_time - start_time
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    logger.info(f"Execution time: {int(hours)}h {int(minutes)}m {int(seconds)}s")
    logger.info(f"Total DCM files moved: {total_moved_files}")


if __name__ == "__main__":
    main()
