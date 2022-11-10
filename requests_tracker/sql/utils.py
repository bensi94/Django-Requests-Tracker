# from django.utils.translation import gettext_lazy as _
#
#
# def get_isolation_level_display(vendor: str, level: int) -> str:
#     if vendor != "postgresql":
#         raise ValueError(vendor)
#     import psycopg2.extensions
#
#     choices = {
#         psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT: _("Autocommit"),
#         psycopg2.extensions.ISOLATION_LEVEL_READ_UNCOMMITTED: _("Read uncommitted"),
#         psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED: _("Read committed"),
#         psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ: _("Repeatable read"),
#         psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE: _("Serializable"),
#     }
#
#     return str(choices.get(level))
#
#
# def get_transaction_status_display(vendor: str, level: int) -> str:
#     if vendor != "postgresql":
#         raise ValueError(vendor)
#     import psycopg2.extensions
#
#     choices = {
#         psycopg2.extensions.TRANSACTION_STATUS_IDLE: _("Idle"),
#         psycopg2.extensions.TRANSACTION_STATUS_ACTIVE: _("Active"),
#         psycopg2.extensions.TRANSACTION_STATUS_INTRANS: _("In transaction"),
#         psycopg2.extensions.TRANSACTION_STATUS_INERROR: _("In error"),
#         psycopg2.extensions.TRANSACTION_STATUS_UNKNOWN: _("Unknown"),
#     }
#
#     return str(choices.get(level))
#
#
# def contrasting_color_generator():
#     """
#     Generate constrasting colors by varying most significant bit of RGB first,
#     and then vary subsequent bits systematically.
#     """
#
#     def rgb_to_hex(rgb):
#         return "#%02x%02x%02x" % tuple(rgb)
#
#     triples = [
#         (1, 0, 0),
#         (0, 1, 0),
#         (0, 0, 1),
#         (1, 1, 0),
#         (0, 1, 1),
#         (1, 0, 1),
#         (1, 1, 1),
#     ]
#     n = 1 << 7
#     so_far = [[0, 0, 0]]
#     while True:
#         if n == 0:  # This happens after 2**24 colours; presumably, never
#             yield "#000000"  # black
#         copy_so_far = list(so_far)
#         for triple in triples:
#             for previous in copy_so_far:
#                 rgb = [n * triple[i] + previous[i] for i in range(3)]
#                 so_far.append(rgb)
#                 yield rgb_to_hex(rgb)
#         n >>= 1
