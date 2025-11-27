from voice_handler import get_user_trigger, load_user_profile
print('get_user_trigger for test.user@example.com ->', get_user_trigger('test.user@example.com'))
try:
    from src.voice_engine import get_voice_engine
    trig = get_user_trigger('test.user@example.com')
    eng = get_voice_engine(user_trigger=trig, user_name='Test')
    print('Voice engine user_trigger:', eng.state.user_trigger)
except Exception as e:
    print('Voice engine import/init failed:', e)
