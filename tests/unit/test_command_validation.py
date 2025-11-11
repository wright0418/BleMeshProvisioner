"""
測試 AT 命令生成是否符合 SDK 文件規格
驗證所有命令的參數順序和格式
"""

import asyncio
from ble_mesh_provisioner.core.async_at_command import (
    async_cmd_get_version,
    async_cmd_get_role,
    async_cmd_mesh_clear,
    async_cmd_start_scan,
    async_cmd_stop_scan,
    async_cmd_open_pbadv,
    async_cmd_provision,
    async_cmd_add_appkey,
    async_cmd_bind_model,
    async_cmd_list_nodes,
    async_cmd_add_subscription,
    async_cmd_remove_subscription,
    async_cmd_set_publish,
    async_cmd_clear_publish,
    async_cmd_send_vendor_data,
)


def test_basic_commands():
    """測試基本命令"""
    print("\n" + "="*60)
    print("基本命令測試")
    print("="*60)

    tests = [
        (async_cmd_get_version(), "AT+VER\r\n"),
        (async_cmd_get_role(), "AT+MRG\r\n"),
        (async_cmd_mesh_clear(), "AT+NR\r\n"),
        (async_cmd_start_scan(), "AT+DIS 1\r\n"),
        (async_cmd_stop_scan(), "AT+DIS 0\r\n"),
    ]

    for cmd, expected in tests:
        result = cmd.raw == expected
        status = "✅" if result else "❌"
        print(f"{status} {cmd.raw.strip():30s} {'OK' if result else 'FAIL'}")
        if not result:
            print(f"   期望: {expected.strip()}")


def test_provisioning_commands():
    """測試 Provisioning 相關命令"""
    print("\n" + "="*60)
    print("Provisioning 命令測試")
    print("="*60)

    tests = [
        # AT+PBADVCON [DEV_UUID]
        (
            async_cmd_open_pbadv("0123456789abcdef"),
            "AT+PBADVCON 0123456789abcdef\r\n"
        ),
        # AT+PROV (無參數)
        (
            async_cmd_provision("0x0100", 5),
            "AT+PROV\r\n"
        ),
        # AT+AKA [dst] [app_key_index] [net_key_index]
        (
            async_cmd_add_appkey("0x0100", 0, 0),
            "AT+AKA 0x0100 0 0\r\n"
        ),
        # AT+MAKB [dst] [element_index] [model_id] [app_key_index]
        (
            async_cmd_bind_model("0x0100", "0", "0x1000", "0"),
            "AT+MAKB 0x0100 0 0x1000 0\r\n"
        ),
        (
            async_cmd_bind_model("0x0100", "0", "0x1000ffff", "0"),
            "AT+MAKB 0x0100 0 0x1000ffff 0\r\n"
        ),
    ]

    for cmd, expected in tests:
        result = cmd.raw == expected
        status = "✅" if result else "❌"
        print(f"{status} {cmd.raw.strip():45s} {'OK' if result else 'FAIL'}")
        if not result:
            print(f"   期望: {expected.strip()}")


def test_subscription_commands():
    """測試訂閱/發佈命令"""
    print("\n" + "="*60)
    print("訂閱/發佈命令測試")
    print("="*60)

    tests = [
        # AT+MSAA [dst] [element_index] [model_id] [Group_addr]
        (
            async_cmd_add_subscription("0x0100", 0, "0x1000", "0xC000"),
            "AT+MSAA 0x0100 0 0x1000 0xC000\r\n"
        ),
        (
            async_cmd_add_subscription("0x0100", 0, "0x1000ffff", "0xC000"),
            "AT+MSAA 0x0100 0 0x1000ffff 0xC000\r\n"
        ),
        # AT+MSAD [dst] [element_index] [model_id] [Group_addr]
        (
            async_cmd_remove_subscription("0x0100", 0, "0x1000", "0xC000"),
            "AT+MSAD 0x0100 0 0x1000 0xC000\r\n"
        ),
        # AT+MPAS [dst] [element_idx] [model_id] [publish_addr] [publish_app_key_idx]
        (
            async_cmd_set_publish("0x0100", 0, "0x1000", "0xC000", 0),
            "AT+MPAS 0x0100 0 0x1000 0xC000 0\r\n"
        ),
        (
            async_cmd_set_publish("0x0100", 0, "0x1000ffff", "0x0101", 0),
            "AT+MPAS 0x0100 0 0x1000ffff 0x0101 0\r\n"
        ),
        # AT+MPAD [dst] [element_idx] [model_id] [publish_app_key_idx]
        (
            async_cmd_clear_publish("0x0100", 0, "0x1000", 0),
            "AT+MPAD 0x0100 0 0x1000 0\r\n"
        ),
    ]

    for cmd, expected in tests:
        result = cmd.raw == expected
        status = "✅" if result else "❌"
        print(f"{status} {cmd.raw.strip():50s} {'OK' if result else 'FAIL'}")
        if not result:
            print(f"   期望: {expected.strip()}")


def test_vendor_data_command():
    """測試 Vendor 數據命令"""
    print("\n" + "="*60)
    print("Vendor 數據命令測試")
    print("="*60)

    tests = [
        # AT+MDTS [dst] [element_index] [app_key_idx] [ack] [data]
        # RGB LED 控制: 0x87 0x01 0x00 0x05 C W R G B
        (
            async_cmd_send_vendor_data(
                "0x0100", 0, 0, 0, "870100050AFF00FF00"),
            "AT+MDTS 0x0100 0 0 0 870100050AFF00FF00\r\n"
        ),
        # Plug 控制: 0x87 0x02 0x00 0x01 [0x01|0x00]
        (
            async_cmd_send_vendor_data("0x0100", 0, 0, 0, "8702000101"),
            "AT+MDTS 0x0100 0 0 0 8702000101\r\n"
        ),
        (
            async_cmd_send_vendor_data("0x0100", 0, 0, 0, "8702000100"),
            "AT+MDTS 0x0100 0 0 0 8702000100\r\n"
        ),
    ]

    for cmd, expected in tests:
        result = cmd.raw == expected
        status = "✅" if result else "❌"
        print(f"{status} {cmd.raw.strip():55s} {'OK' if result else 'FAIL'}")
        if not result:
            print(f"   期望: {expected.strip()}")


def test_list_nodes_command():
    """測試列出節點命令"""
    print("\n" + "="*60)
    print("列出節點命令測試")
    print("="*60)

    cmd = async_cmd_list_nodes()
    expected = "AT+NL\r\n"
    result = cmd.raw == expected
    status = "✅" if result else "❌"
    print(f"{status} {cmd.raw.strip():30s} {'OK' if result else 'FAIL'}")
    if not result:
        print(f"   期望: {expected.strip()}")


def main():
    """主測試函數"""
    print("\n" + "="*60)
    print("AT 命令格式驗證測試")
    print("="*60)

    test_basic_commands()
    test_provisioning_commands()
    test_subscription_commands()
    test_vendor_data_command()
    test_list_nodes_command()

    print("\n" + "="*60)
    print("測試完成")
    print("="*60)


if __name__ == "__main__":
    main()
