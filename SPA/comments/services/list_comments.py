from django.core.paginator import Paginator
from django.db.models import Q

from comments.models import Comment


PAGE_SIZE = 25
SORT_FIELDS = {
    "newest": ("-created_at", "-id"),
    "oldest": ("created_at", "id"),
    "username_asc": ("username", "-created_at", "-id"),
    "username_desc": ("-username", "-created_at", "-id"),
    "email_asc": ("email", "-created_at", "-id"),
    "email_desc": ("-email", "-created_at", "-id"),
}


def comment_page_number(comment_id, sort="newest"):
    """Find a reply's root and its page using the list's exact sort/tie-breakers."""
    seen = set()
    while True:
        if comment_id in seen:
            raise Comment.DoesNotExist("The comment's thread contains a cycle.")
        seen.add(comment_id)
        root = Comment.objects.get(pk=comment_id)
        if root.parent_id is None:
            break
        comment_id = root.parent_id
    preceding, equal = Q(), Q()
    for field in SORT_FIELDS.get(sort, SORT_FIELDS["newest"]):
        name = field.lstrip("-")
        comparison = "gt" if field.startswith("-") else "lt"
        value = getattr(root, name)
        preceding |= equal & Q(**{f"{name}__{comparison}": value})
        equal &= Q(**{name: value})
    return Comment.objects.filter(parent__isnull=True).filter(preceding).count() // PAGE_SIZE + 1


def get_comment_page(number=1, sort="newest"):
    # Never pass request values directly to order_by or SQL. Roots are paginated
    # separately so replies stay together; render data is built by the serializer.

    ordering = SORT_FIELDS.get(sort, SORT_FIELDS["newest"])
    queryset = Comment.objects.select_related("quoted_comment", "attachment")
    roots = queryset.filter(parent__isnull=True).order_by(*ordering)
    page = Paginator(roots, PAGE_SIZE).get_page(number)
    page.object_list = list(page.object_list)
    page.replies_by_parent = {}
    current = page.object_list
    seen = set()
    while current:
        parents = {comment.pk for comment in current}
        seen.update(parents)
        # One query per level, rather than one per comment. A recursive PostgreSQL
        # CTE would be a suitable replacement when threads become much larger.
        children = list(queryset.filter(parent_id__in=parents).exclude(pk__in=seen)
                        .order_by("created_at", "id"))
        for child in children:
            page.replies_by_parent.setdefault(child.parent_id, []).append(child)
        current = children
    return page
