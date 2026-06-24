from writers.models import PointLog
from django.utils import timezone

TODAY_MESSAGES = [
    "오늘은 어떤 고민을 전달해볼까요?",
    "소중한 고민이 깨지지 않게 배송할게요!",
    "오늘의 고민은 무엇인가요?",
    "똑똑! 워리양입니다. 반가워요!",
    "꽁꽁 묵혀둔 고민, 얼른 보내버려요.",
    "워리양과 함께 고민 해결해요!",
    "마음속 고민, 저희가 대신 배송할게요.",
    "고민은 가져가고, 위로를 배달할게요.",
    "비우고 싶은 고민을 담아 보내주세요.",
    "오늘의 고민도 안전하게 보내드릴게요.",
    ]

Yang = {
    "new_yang": {
        "name": "신규 유저",
        "price": 0,
        "image": "images/newbie.png",
        "description": "",
    },
    "young_yang": {
        "name": "어린양",
        "price": 5,
        "image": "images/worryang1.png",
        "description": "하루 당 +1 고민",
    },
    "very_yang": {
        "name": "버리양",
        "price": 20,
        "image": "images/store_2.png",
        "description": "하루 당 +3 고민",
    },
    "worry_yang": {
        "name": "워리양",
        "price": 50,
        "image": "images/store_3.png",
        "description": "하루 당 +5 고민\n새벽 배송 입장 가능",
    },
}

"""
[포인트 증감 함수]
- 기능: profile 객체의 포인트를 points 만큼 증감
"""
def edit_points(profile, source, amount):
    if amount >= 0:
        point_type = "EARN"
    else:
        point_type = "USE"
    
    # 잔액 부족시
    if profile.points + amount < 0:
        return False
    
    profile.points += amount
    profile.save()

    point_log = PointLog()
    point_log.writer = profile.writer
    point_log.point_type = point_type
    point_log.source = source
    point_log.amount = amount
    point_log.points_after = profile.points

    point_log.save()
    return True

"""
    [시간 계산 util 함수]
    - 기능: 현재 시간 기준 작성하고 얼마나 지났는지 계산
"""
def get_time_ago(pub_date):
    now = timezone.now()

    diff = now - pub_date
    seconds = diff.days * 24 * 60 * 60 + diff.seconds

    if seconds < 60:
        return "방금 전"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}분 전"

    hours = minutes // 60
    if hours < 24:
        return f"{hours}시간 전"

    days = hours // 24
    if days < 7:
        return f"{days}일 전"

    weeks = days // 7
    if weeks < 5:
        return f"{weeks}주 전"

    return str(pub_date.year) + "." + str(pub_date.month) + "." + str(pub_date.day)