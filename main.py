from finances.config import SOURCE_STATEMENTS_PATH, PREPROCESSED_STATEMENTS_PATH
from finances.csv_loading import load_all_csv_files
from finances.preprocessing import preprocess_and_save
from finances.sunburst import create_transaction_sunburst


if __name__ == "__main__":
    df = load_all_csv_files(SOURCE_STATEMENTS_PATH)

    preprocess_and_save(df, PREPROCESSED_STATEMENTS_PATH)

    create_transaction_sunburst(df).show()
