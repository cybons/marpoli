from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Service:
    name: str
    port: int

@dataclass
class Rule:
    name: str
    sources: List[str] = field(default_factory=list)
    destinations: List[str] = field(default_factory=list)
    services: List[Service] = field(default_factory=list)
    users: List[str] = field(default_factory=list)
    source_zones: List[str] = field(default_factory=list)
    destination_zones: List[str] = field(default_factory=list)

@dataclass
class PaloaltConfig:
    before_kyoto: List[Rule] = field(default_factory=list)
    after_kyoto: List[Rule] = field(default_factory=list)
    before_tokyo: List[Rule] = field(default_factory=list)
    after_tokyo: List[Rule] = field(default_factory=list)

# 差分計算のクラスもデータクラスとして定義可能
@dataclass
class RuleDifference:
    name: str
    added: bool = False
    removed: bool = False
    changes: Dict[str, Any] = field(default_factory=dict)

class RuleDiffCalculator:
    def __init__(self, before: List[Rule], after: List[Rule]):
        self.before_map = {rule.name: rule for rule in before}
        self.after_map = {rule.name: rule for rule in after}
        self.added: List[Rule] = []
        self.removed: List[Rule] = []
        self.modified: List[RuleDifference] = []

    def compute_diff(self):
        # 追加されたルール
        for name, rule in self.after_map.items():
            if name not in self.before_map:
                self.added.append(rule)

        # 削除されたルール
        for name, rule in self.before_map.items():
            if name not in self.after_map:
                self.removed.append(rule)

        # 変更されたルール
        for name in self.before_map.keys() & self.after_map.keys():
            before_rule = self.before_map[name]
            after_rule = self.after_map[name]
            differences = self.compare_rules(before_rule, after_rule)
            if differences:
                self.modified.append(RuleDifference(name=name, changes=differences))

    def compare_rules(self, before: Rule, after: Rule) -> Dict[str, Any]:
        changes = {}
        attributes = ['sources', 'destinations', 'services', 'users', 'source_zones', 'destination_zones']
        for attr in attributes:
            before_value = getattr(before, attr)
            after_value = getattr(after, attr)
            if isinstance(before_value, list) and isinstance(after_value, list):
                added_items = list(set(after_value) - set(before_value))
                removed_items = list(set(before_value) - set(after_value))
                if added_items or removed_items:
                    changes[attr] = {
                        'added': added_items,
                        'removed': removed_items
                    }
            else:
                if before_value != after_value:
                    changes[attr] = {
                        'before': before_value,
                        'after': after_value
                    }
        return changes

# 使用例
if __name__ == "__main__":
    # サンプルデータの作成
    service1 = Service(name="HTTP", port=80)
    service2 = Service(name="HTTPS", port=443)

    before_rule_kyoto = Rule(
        name="Allow_HTTP",
        sources=["10.0.0.1"],
        destinations=["10.0.0.2"],
        services=[service1],
        users=["user1"],
        source_zones=["zone1"],
        destination_zones=["zone2"]
    )

    after_rule_kyoto = Rule(
        name="Allow_HTTP",
        sources=["10.0.0.1"],
        destinations=["10.0.0.2"],
        services=[service1, service2],  # サービスが追加
        users=["user1", "user2"],       # ユーザーが追加
        source_zones=["zone1"],
        destination_zones=["zone2"]
    )

    config = PaloaltConfig(
        before_kyoto=[before_rule_kyoto],
        after_kyoto=[after_rule_kyoto],
        before_tokyo=[],
        after_tokyo=[]
    )

    # 差分計算
    kyoto_diff = RuleDiffCalculator(config.before_kyoto, config.after_kyoto)
    kyoto_diff.compute_diff()

    print("京都の追加ルール:")
    for rule in kyoto_diff.added:
        print(f"  {rule.name}")

    print("京都の削除ルール:")
    for rule in kyoto_diff.removed:
        print(f"  {rule.name}")

    print("京都の変更ルール:")
    for diff in kyoto_diff.modified:
        print(f"  ルール名: {diff.name}")
        for attr, change in diff.changes.items():
            print(f"    属性: {attr}")
            if 'added' in change or 'removed' in change:
                if change['added']:
                    print(f"      追加: {change['added']}")
                if change['removed']:
                    print(f"      削除: {change['removed']}")
            else:
                print(f"      Before: {change['before']}")
                print(f"      After: {change['after']}")