def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def merge_docs(docs, n):
    for i in range(0, len(docs), n):
        yield " ".join(docs[i:i + n]).replace('\n', '')


def flatten(full_list):
    return [item for sub_list in full_list for item in sub_list]
