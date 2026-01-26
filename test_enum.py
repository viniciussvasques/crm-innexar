
import enum
class SiteOrderStatus(str, enum.Enum):
    PENDING_PAYMENT = "pending_payment"
    GENERATING = "generating"

print(f"Value of GENERATING: '{SiteOrderStatus.GENERATING}'")
print(f"Type of GENERATING: {type(SiteOrderStatus.GENERATING)}")
print(f"Is instance of str? {isinstance(SiteOrderStatus.GENERATING, str)}")
print(f"String representation: {str(SiteOrderStatus.GENERATING)}")
