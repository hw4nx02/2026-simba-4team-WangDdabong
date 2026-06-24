from django.urls import path
from .views import *

app_name = "worries"

urlpatterns = [
    path("post_worry/", post_worry, name="post_worry"),
    path("get_worries/", get_worries, name="get_worries"),
    path("post_bookmark/<int:worry_id>", post_bookmark, name="post_bookmark"),
    path("post_cheerup/<int:worry_id>", post_cheerup, name="post_cheerup"),
    path("get_worry_detail/<int:worry_id>", get_worry_detail, name="get_worry_detail"),
    path("hall_of_fame/", hall_of_fame, name="hall_of_fame"),
    path("hall_of_fame_entry/", hall_of_fame_entry, name="hall_of_fame_entry"),
    path("hall_of_fame_card/<int:epilogue_id>", hall_of_fame_card, name="hall_of_fame_card"),
    path("post_answer/<int:worry_id>", post_answer, name="post_answer"),
    path("edit_satisfaction/<int:answer_id>/<int:is_satisfied>", edit_satisfaction, name="edit_satisfaction"),
    path('postbox/', postbox, name='postbox'),
]