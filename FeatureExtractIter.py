import torch
from torch.autograd import Variable
from thread import start_new_thread
try:
    import queue
except ImportError:
    import Queue as queue


class FeatureExtractIter(object):
    def __init__(self, dataloader, extractor, dev_id, max_queue_size=2):
        assert isinstance(dataloader, torch.utils.data.DataLoader)
        assert isinstance(extractor, torch.nn.Module)
        self.q = queue.Queue(maxsize=max_queue_size)
        start_new_thread(extract_feature, (dataloader, self.q, extractor, dev_id))

    def __iter__(self):
        return self

    def __next__(self):
        obj = self.q.get()
        if obj is None:
            raise StopIteration
        else:
            return obj

    next = __next__


def extract_feature(dataloader, q, extractor, dev_id):
    """ Note that we should change collate_fn so that 
        input2s: [mini-mini-batch1,...,mini-mini-batch4] """
    try:
        for i, (input1, input2s, target) in enumerate(dataloader, 0):
            out = []
            for x in input2s:
                x = Variable(x, volatile=True)
                x = x.cuda(dev_id)
                out.append(extractor(x).cpu())
            out = torch.cat(out, 0)
            q.put((input1, out, target))
    except KeyboardInterrupt:
        dataloader._shutdown_workers()
    finally:
        q.put(None)


"""Sample of collate_fn"""
# from torch.utils.data.dataloader import default_collate
# mini_mini_batch_size=64
# def collate_fn(batch):
#     imgs, targets=default_collate(batch)
#     out=[ imgs[i:(i+mini_mini_batch_size)]
#           for i in xrange(0, len(imgs) , mini_mini_batch_size) ]
#     return imgs, out, targets
