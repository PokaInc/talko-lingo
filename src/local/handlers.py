def rx(event, context):
    from rx import rx
    rx.dummy_handler(event, context)


def tx(event, context):
    from tx import tx
    tx.dummy_handler(event, context)
