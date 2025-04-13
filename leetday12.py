class Solution:
    def mySqrt(self, x: int) -> int:
        if x == 0 or x == 1:
            return x

        start, end = 0, x
        ans = 0

        while start <= end:
            mid = (start + end) // 2

            if mid * mid == x:
                return mid

            elif mid * mid < x:
                ans = mid
                start = mid + 1

            else:
                end = mid - 1

        return ans

        