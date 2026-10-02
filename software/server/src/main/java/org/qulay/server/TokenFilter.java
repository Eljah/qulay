package org.qulay.server;
import org.springframework.beans.factory.annotation.Value;import org.springframework.stereotype.Component;import org.springframework.web.filter.OncePerRequestFilter;
import jakarta.servlet.*;import jakarta.servlet.http.*;import java.io.*;import java.nio.charset.StandardCharsets;import java.security.MessageDigest;
@Component public class TokenFilter extends OncePerRequestFilter {
 private final byte[] expected;private final boolean dev;
 public TokenFilter(@Value("${qulay.token}")String token,@Value("${qulay.dev-mode}")boolean dev){this.dev=dev;if(!dev&&token.length()<24)throw new IllegalStateException("Set QULAY_TOKEN to at least 24 characters; no production default token exists");expected=("Bearer "+token).getBytes(StandardCharsets.UTF_8);}
 @Override protected void doFilterInternal(HttpServletRequest req,HttpServletResponse res,FilterChain chain)throws ServletException,IOException{
  res.setHeader("X-Content-Type-Options","nosniff");res.setHeader("Referrer-Policy","no-referrer");res.setHeader("Cache-Control","no-store");
  if(req.getRequestURI().startsWith("/api/")&&!dev){String v=req.getHeader("Authorization");if(v==null||!MessageDigest.isEqual(expected,v.getBytes(StandardCharsets.UTF_8))){res.setStatus(401);res.setContentType("application/json");res.getWriter().write("{\"error\":\"unauthorized\"}");return;}}
  chain.doFilter(req,res);
 }
}
