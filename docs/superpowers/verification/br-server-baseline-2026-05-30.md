# br-server 重构基线验证

- `..\env\python.exe -m pytest tests/test_booking_payment_service.py -q`：通过，10 passed，1 个 `.pytest_cache` 权限警告。
- `..\env\python.exe -m pytest tests/test_wallet_service.py -q`：通过，18 passed，1 个 `.pytest_cache` 权限警告。
- `..\env\python.exe -m pytest tests/test_booking_verification_service.py -q`：通过，19 passed，1 个 `.pytest_cache` 权限警告。
- `..\env\python.exe -m pytest tests/test_api_booking.py -q`：失败，40 passed，1 failed，2 个 `.pytest_cache` 权限警告。

失败用例：

- `tests/test_api_booking.py::TestListBookings::test_list_bookings_filter_by_status`
- 断言：`assert data["total"] == 1`
- 实际：`data["total"] == 0`

备注：

- 当前工作区使用根目录 `env` 环境运行测试：`D:\Workspaces\booking-room\env\python.exe`。
- 直接运行系统 `python -m pytest` 会失败，原因是系统 Python 环境没有安装 `pytest`。
- `.pytest_cache` 目录存在权限问题，pytest 无法写入缓存，但前三组测试仍可完成。
