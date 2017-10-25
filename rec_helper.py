# -*- coding: utf-8 -*-
"""
Created on Mon Oct 23 16:00:22 2017

@author: 116952
"""
#%%
# =============================================================================
# helper function 
# =============================================================================
import numpy as np 
import  scipy.sparse as sp
from sklearn.preprocessing import binarize
def threshold_interaction(df,rowname,colname,row_min=1):
    """limit interaction(u-i) dataframe greater than row_min numbers 
    
    Parameters
    ----------
    df: Dataframe
         purchasing dataframe         
    rowname: 
        name of user(Uid)
    colname: 
        name of item(Iid)
    row_min:
        min numbers        
    """
    n_rows = df[rowname].unique().shape[0]
    n_cols = df[colname].unique().shape[0]
    sparsity = float(df.shape[0]) / float(n_rows*n_cols) * 100
    print('Starting interactions info')
    print('Number of rows: {}'.format(n_rows))
    print('Number of cols: {}'.format(n_cols))
    print('Sparsity: {:4.2f}%'.format(sparsity))

    df_groups = df.groupby([rowname,colname])[colname].count()
    row_counts = df_groups.groupby(rowname).count()
#    col_counts = df.groupby(colname)[rowname]
    uids = row_counts[row_counts > row_min].index.tolist() # lists of uids purchasing item greater than row_min
    
    df2 = df[df[rowname].isin(uids)]
    
    n_rows2 = df2[rowname].unique().shape[0]
    n_cols2 = df2[colname].unique().shape[0]
    sparsity2 = float(df2.shape[0]) / float(n_rows2*n_cols2) * 100
    print('Ending interactions info')
    print('Number of rows: {}'.format(n_rows2))
    print('Number of columns: {}'.format(n_cols2))
    print('Sparsity: {:4.2f}%'.format(sparsity2))
    
    return df2

def df_to_spmatrix(df, rowname, colname):
    """convert dataframe to sparse (interaction) matrix
    
    Pamrameters
    -----------
    df: Dataframe
        
    Returns:
    -----------
    interaction : sparse csr matrix
        
    rid_to_idx : dict
        Map row ID to idx in the interaction matrix
    idx_to_rid : dict
    cid_to_idx : dict
    idx_to_cid :dict
    """
    rids = df[rowname].unique().tolist() # lists of rids 
    cids = df[colname].unique().tolist() # lists of cids
    
    ### map row/column id to idx ###
    rid_to_idx = {}
    idx_to_rid = {}
    for (idx, rid) in enumerate(rids):
        rid_to_idx[rid] = idx
        idx_to_rid[idx] = rid
        
    cid_to_idx = {}
    idx_to_cid = {}
    for (idx, cid) in enumerate(cids):
        cid_to_idx[cid] = idx
        idx_to_cid[idx] = cid
        
    ### 
    
    def map_ids(row, mapper):
        return mapper[row]
    
    I = df[rowname].apply(map_ids, args=[rid_to_idx]).as_matrix()
    J = df[colname].apply(map_ids, args=[cid_to_idx]).as_matrix()
    V = np.ones(I.shape[0])    
    interactions = sp.coo_matrix((V,(I,J)),dtype='int32')
    interactions = binarize(interactions) # also coo convert to csr 
#    interactions = interactions.tocsr()
    
    return interactions,rid_to_idx,idx_to_rid,cid_to_idx,idx_to_cid


def train_test_split(sp_interaction, split_count, fraction=None):
    """ split interaction data into train and test sets 
    
    Parameters
    ----------
    sp_interaction: csr sparse matrix
    split_count: int
        Number of u-i interaction per user to move from original sets 
        to test set.
    fractions: float
        Fractions of users to split off into test sets.
        If None, all users are considered. 
    """
    train = sp_interaction.copy().tocoo()
    test = sp.lil_matrix(train.shape)  
    
    if fraction:
        try:
            user_idxs = np.random.choice(
                np.where(np.bincount(train.row) >= split_count * 2)[0],
                replace=False,
                size=np.int64(np.floor(fraction * train.shape[0]))
            ).tolist()
        except:
            print(('Not enough users with > {} '
                  'interactions for fraction of {}')\
                  .format(2*split_count, fraction))
            raise
    else:
        user_idxs = range(sp_interaction.shape[0])
        
    train = train.tolil()
    for uidx in user_idxs:
        test_interactions = np.random.choice(sp_interaction.getrow(uidx).indices,
                                        size=split_count,
                                        replace=False)
        train[uidx, test_interactions] = 0.
        test[uidx, test_interactions] = sp_interaction[uidx, test_interactions]
        
    # Test and training are truly disjoint
    assert(train.multiply(test).nnz == 0)
    return train.tocsr(), test.tocsr(), user_idxs

def print_log(row, header=False, spacing=12):
    top = ''
    middle = ''
    bottom = ''
    for r in row:
        top += '+{}'.format('-'*spacing)
        if isinstance(r, str):
            middle += '| {0:^{1}} '.format(r, spacing-2)
        elif isinstance(r, int):
            middle += '| {0:^{1}} '.format(r, spacing-2)
        elif (isinstance(r, float)
              or isinstance(r, np.float32)
              or isinstance(r, np.float64)):
            middle += '| {0:^{1}.5f} '.format(r, spacing-2)
        bottom += '+{}'.format('='*spacing)
    top += '+'
    middle += '|'
    bottom += '+'
    if header:
        print(top)
        print(middle)
        print(bottom)
    else:
        print(middle)
        print(top)
