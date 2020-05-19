import csv
import pandas as panda 

def load_book_data_from_csv(fname, tbl_name, engine):
    print('Opening local books file...')
    f = ''
    try: 
        f = open(fname, 'r+')
    except: 
        print('Was unable to open the input csv file!')

    data_f = panda.read_csv(f)
    data_f.to_sql(tbl_name, con=engine, index=True, index_label='id', if_exists='replace')
    return 


# if __name__ == "__main__":  
#     load_book_data_from_csv('books.csv')