using System;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using FirebaseAdmin.Auth;

namespace CustomAuthService
{
    [Route("login")]
    public class LoginController : ControllerBase
    {
        private readonly UserStore userStore = new UserStore();

        [HttpPost]
        public async Task<ActionResult> Login([FromBody] LoginRequest request)
        {
            try
            {
                var user = await this.userStore.LoginAsync(request);
                var token = await FirebaseAuth.DefaultInstance.CreateCustomTokenAsync(
                    user.Uid, user.Claims);
                return this.Ok(new LoginResult()
                {
                    CustomToken = token,
                });
            }
            catch (Exception e)
            {
                return this.StatusCode(401, new { Error = e.Message });
            }
        }
    }

    public class LoginRequest
    {
        public string Username { get; set; }

        public string Password { get; set; }
    }

    public class LoginResult
    {
        public string CustomToken { get; set; }
    }
}