class UsernameService:

    PREFIX = "vpn"
    WIDTH = 6

    def generate(
        self,
        user_id: int,
    ) -> str:

        return f"{self.PREFIX}_{user_id:0{self.WIDTH}d}"