# Source

UE5 游戏模块以后放在 `Source/NeonRift/`。

本仓没有 `.uproject`，所以这里还没有 `.Build.cs`，也没有假装能编译的空模块。下一份 Codex 提交才会加入 C++，并实现 `docs/rules/UE_EVENT_WIRING.md` 里的事件。在那之前，权威规则是 `sim/steel_tide`。

预留名字，现在都还不存在于工程里：

- `UNeonRiftMatchSubsystem`
- `UNeonRiftRulesConfig`
- `ANeonRiftCore`
- `ANeonRiftTerminal`
- `ANeonRiftBridgeSpan`

操作员不要用关卡蓝图实现同名逻辑来代替这个模块。
