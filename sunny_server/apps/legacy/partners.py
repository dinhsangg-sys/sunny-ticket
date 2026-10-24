import copy

DEFAULT_TYPES = [
    {'id':'travel_agency','name':'Đại lý du lịch','active':True},
    {'id':'tour_guide','name':'Hướng dẫn viên','active':True},
    {'id':'accommodation','name':'Khách sạn / lưu trú','active':True},
    {'id':'individual','name':'Cộng tác viên cá nhân','active':True},
    {'id':'other','name':'Khác','active':True},
]

def partner_types(data):
    return data.get('partnerTypes',copy.deepcopy(DEFAULT_TYPES))

def enforce_partner_types(before,after):
    types={t['id']:t for t in partner_types(after)}
    old_agents={a['id']:a for a in before.get('agents',[])}
    for a in after.get('agents',[]):
        key=a.get('partnerTypeId','')
        if not key: continue  # Existing records stay unclassified until explicitly assigned.
        if key not in types: raise ValueError('Loại đối tác không tồn tại.')
        old_key=old_agents.get(a['id'],{}).get('partnerTypeId')
        if key!=old_key and not types[key].get('active',True): raise ValueError('Không thể gán loại đối tác đã ngừng dùng.')
    for a in before.get('agents',[]):
        if a.get('partnerTypeId') and a['partnerTypeId'] not in types: raise ValueError('Loại đối tác đã dùng chỉ được ngừng, không được xóa.')
