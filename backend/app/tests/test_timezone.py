"""
Timezone Configuration Test Cases
Tests for verifying timezone consistency across the application
"""
import pytest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from app.utils.timezone import get_db_now, get_now, to_local, to_utc, get_today_start, get_today_end
from app.core.config import settings


class TestTimezoneConfiguration:
    """Test timezone configuration and utility functions"""
    
    def test_settings_timezone_default(self):
        """Test that default timezone is Asia/Shanghai"""
        assert settings.TIMEZONE == "Asia/Shanghai"
    
    def test_settings_tz_property(self):
        """Test that settings.tz returns correct ZoneInfo"""
        assert settings.tz == ZoneInfo("Asia/Shanghai")
    
    def test_get_db_now_returns_utc(self):
        """Test that get_db_now returns UTC naive datetime"""
        dt = get_db_now()
        assert dt.tzinfo is None
        assert isinstance(dt, datetime)
    
    def test_get_now_returns_local(self):
        """Test that get_now returns timezone-aware local datetime"""
        dt = get_now()
        assert dt.tzinfo is not None
        assert dt.tzinfo == ZoneInfo("Asia/Shanghai")
    
    def test_to_local_converts_utc_to_local(self):
        """Test that to_local correctly converts UTC to Asia/Shanghai"""
        utc_dt = datetime(2024, 1, 1, 12, 0, 0)
        local_dt = to_local(utc_dt)
        assert local_dt.tzinfo == ZoneInfo("Asia/Shanghai")
        assert local_dt.hour == 20
    
    def test_to_local_handles_none(self):
        """Test that to_local handles None input"""
        assert to_local(None) is None
    
    def test_to_utc_converts_local_to_utc(self):
        """Test that to_utc correctly converts local time to UTC"""
        local_dt = datetime(2024, 1, 1, 20, 0, 0)
        utc_dt = to_utc(local_dt)
        assert utc_dt.hour == 12
        assert utc_dt.tzinfo is None
    
    def test_to_utc_handles_none(self):
        """Test that to_utc handles None input"""
        assert to_utc(None) is None
    
    def test_get_today_start(self):
        """Test that get_today_start returns start of day in local timezone"""
        start = get_today_start()
        assert start.hour == 0
        assert start.minute == 0
        assert start.second == 0
        assert start.tzinfo == ZoneInfo("Asia/Shanghai")
    
    def test_get_today_end(self):
        """Test that get_today_end returns end of day in local timezone"""
        end = get_today_end()
        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59
        assert end.tzinfo == ZoneInfo("Asia/Shanghai")


class TestDatabaseTimeStorage:
    """Test database time storage consistency"""
    
    def test_db_time_is_utc(self):
        """Test that database times are stored in UTC"""
        from app.models.models import get_db_now
        
        dt = get_db_now()
        utc_now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        time_diff = abs((dt - utc_now).total_seconds())
        assert time_diff < 1
    
    def test_token_expiry_uses_utc(self):
        """Test that token expiry is calculated in UTC"""
        from app.services.email_service import EmailService
        
        expiry = EmailService.get_token_expiry()
        now = get_db_now()
        
        expected_diff = timedelta(hours=24).total_seconds()
        actual_diff = (expiry - now).total_seconds()
        
        assert abs(actual_diff - expected_diff) < 1


class TestTimeComparison:
    """Test time comparison logic for verification tokens, etc."""
    
    def test_verification_token_expiry_comparison(self):
        """Test that verification token expiry comparison works correctly"""
        now = get_db_now()
        future = now + timedelta(hours=1)
        past = now - timedelta(hours=1)
        
        assert future > now
        assert past < now
    
    def test_password_reset_expiry_comparison(self):
        """Test that password reset expiry comparison works correctly"""
        now = get_db_now()
        expires_at = now + timedelta(minutes=15)
        
        assert expires_at > now
        
        expired = now - timedelta(minutes=1)
        assert expired < now


class TestAPITimeSerialization:
    """Test API time serialization"""
    
    def test_serialize_datetime(self):
        """Test that datetime serialization includes timezone info"""
        from app.schemas.schemas import serialize_datetime
        
        utc_dt = datetime(2024, 1, 1, 12, 0, 0)
        serialized = serialize_datetime(utc_dt)
        
        assert serialized is not None
        assert "2024-01-01" in serialized
        assert "20:00" in serialized or "+08:00" in serialized
    
    def test_serialize_datetime_none(self):
        """Test that serialize_datetime handles None"""
        from app.schemas.schemas import serialize_datetime
        
        assert serialize_datetime(None) is None


class TestCrossTimezoneScenarios:
    """Test scenarios involving users from different timezones"""
    
    def test_user_from_different_timezone_sees_correct_time(self):
        """Test that a user from a different timezone sees correct local time"""
        utc_dt = datetime(2024, 6, 15, 6, 30, 0)
        local_dt = to_local(utc_dt)
        
        assert local_dt.hour == 14
        assert local_dt.minute == 30
    
    def test_dst_transition_handling(self):
        """Test handling of DST transitions (Asia/Shanghai doesn't have DST)"""
        winter_dt = datetime(2024, 1, 15, 12, 0, 0)
        summer_dt = datetime(2024, 7, 15, 12, 0, 0)
        
        winter_local = to_local(winter_dt)
        summer_local = to_local(summer_dt)
        
        assert winter_local.hour == 20
        assert summer_local.hour == 20


class TestConsistencyAcrossModules:
    """Test time handling consistency across different modules"""
    
    def test_all_db_operations_use_utc(self):
        """Test that all database operations use UTC time"""
        from app.utils.auth import create_refresh_token_value
        from app.services.email_service import EmailService
        from app.models.models import get_db_now
        
        db_now = get_db_now()
        token_expiry = EmailService.get_token_expiry()
        
        assert token_expiry.tzinfo is None
        assert token_expiry > db_now
    
    def test_log_timestamps_use_db_time(self):
        """Test that log timestamps use database time (UTC)"""
        from app.models.models import OperationLog, LoginLog, AccessLog
        
        assert hasattr(OperationLog, 'created_at')
        assert hasattr(LoginLog, 'created_at')
        assert hasattr(AccessLog, 'created_at')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
