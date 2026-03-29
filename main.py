from finances.config import PATHS
from finances.csv_loading import load_all_csv_files
from finances.preprocessing import preprocess_and_save
from finances.sunburst import create_transaction_sunburst


if __name__ == "__main__":
    df = load_all_csv_files(PATHS.SOURCE_STATEMENTS)
    preprocess_and_save(df, PREPROCESSED_STATEMENTS_PATH)

    create_transaction_sunburst(df).show()
